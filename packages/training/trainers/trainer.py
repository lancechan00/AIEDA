"""第一阶段最小训练器。"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np


def _rel_path_for_summary(path: Union[Path, str]) -> str:
    """将路径转为相对路径，便于开源可移植。"""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ...evaluation import compute_metrics
from ...models import get_backend
from ..config import TrainingConfig
from ..datasets import PCBDatasetBuilder

logger = logging.getLogger(__name__)


class Trainer:
    """只服务第一阶段 `LocalRouteChoiceLite`。"""

    def __init__(self, config: TrainingConfig, output_dir: Optional[str] = None) -> None:
        self.config = config
        self.output_dir = Path(output_dir or config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

        self._set_seed(config.seed)
        self.device = self._setup_device()
        self.model = self._setup_model()
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.criterion = nn.CrossEntropyLoss()
        self.best_accuracy = float("-inf")
        self.history = []

    def _set_seed(self, seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    def _setup_device(self) -> torch.device:
        if self.config.device == "cpu":
            return torch.device("cpu")
        if torch.cuda.is_available() and self.config.device in {"auto", "cuda"}:
            return torch.device("cuda")
        return torch.device("cpu")

    def _setup_model(self) -> nn.Module:
        backend_cls = get_backend(self.config.model_name)
        model = backend_cls(
            modalities=self.config.modalities,
            hidden_dim=self.config.hidden_dim,
            num_classes=self.config.num_classes,
            task_type=self.config.task_type,
            geometry_channels=self.config.geometry_channels,
            image_channels=self.config.image_channels,
        )
        if getattr(model, "supports_training", True) is False:
            raise ValueError(f"{self.config.model_name} 当前是实验后端占位，不参与正式训练")
        return model.to(self.device)

    def _build_loader(self, split: str, shuffle: bool) -> DataLoader:
        dataset = PCBDatasetBuilder.create_dataset(self.config.dataset_path, split=split)
        return PCBDatasetBuilder.create_data_loader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=self.config.num_workers,
        )

    def train(self) -> Dict[str, Any]:
        train_loader = self._build_loader("train", shuffle=True)
        val_loader = self._build_loader("val", shuffle=False)

        for epoch in range(1, self.config.epochs + 1):
            train_metrics = self._run_epoch(train_loader, training=True)
            val_metrics = self._run_epoch(val_loader, training=False)

            epoch_record = {
                "epoch": epoch,
                "train": train_metrics,
                "val": val_metrics,
            }
            self.history.append(epoch_record)
            logger.info(
                "epoch=%s train_acc=%.4f val_acc=%.4f val_top3=%.4f",
                epoch,
                train_metrics["accuracy"],
                val_metrics["accuracy"],
                val_metrics["top_3_accuracy"],
            )

            self._save_checkpoint("last_model.pt", epoch, val_metrics)
            if self.config.save_best_model and val_metrics["accuracy"] >= self.best_accuracy:
                self.best_accuracy = val_metrics["accuracy"]
                self._save_checkpoint("best_model.pt", epoch, val_metrics)

        summary = {
            "history": self.history,
            "best_accuracy": self.best_accuracy,
            "output_dir": _rel_path_for_summary(self.output_dir),
        }
        self._save_summary(summary)
        return summary

    def _run_epoch(self, loader: DataLoader, training: bool) -> Dict[str, float]:
        self.model.train(training)
        logits_list = []
        labels_list = []
        running_loss = 0.0

        for step, batch in enumerate(loader, start=1):
            batch = self._move_batch_to_device(batch)
            outputs = self.model(batch)
            logits = outputs["logits"]
            labels = batch["label"]
            loss = self.criterion(logits, labels)

            if training:
                self.optimizer.zero_grad()
                loss.backward()
                if self.config.gradient_clip_norm > 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip_norm)
                self.optimizer.step()

            running_loss += loss.item()
            logits_list.append(logits.detach().cpu())
            labels_list.append(labels.detach().cpu())

            if training and step % self.config.log_every_n_steps == 0:
                logger.info("step=%s loss=%.4f", step, loss.item())

        if not logits_list:
            return {
                "loss": running_loss / max(len(loader), 1),
                "accuracy": 0.0,
                "top_3_accuracy": 0.0,
            }
        epoch_logits = torch.cat(logits_list, dim=0)
        epoch_labels = torch.cat(labels_list, dim=0)
        metrics = compute_metrics(epoch_logits, epoch_labels)
        metrics["loss"] = running_loss / max(len(loader), 1)
        return metrics

    def _move_batch_to_device(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        moved = {}
        for key, value in batch.items():
            moved[key] = value.to(self.device) if isinstance(value, torch.Tensor) else value
        return moved

    def evaluate(self, split: str = "test", checkpoint_path: Optional[str] = None) -> Dict[str, float]:
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        loader = self._build_loader(split, shuffle=False)
        return self._run_epoch(loader, training=False)

    def predict(self, split: str = "test", checkpoint_path: Optional[str] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        loader = self._build_loader(split, shuffle=False)
        self.model.eval()
        logits_list = []
        labels_list = []
        with torch.no_grad():
            for batch in loader:
                batch = self._move_batch_to_device(batch)
                outputs = self.model(batch)
                logits_list.append(outputs["logits"].detach().cpu())
                labels_list.append(batch["label"].detach().cpu())
        return torch.cat(logits_list, dim=0), torch.cat(labels_list, dim=0)

    def load_checkpoint(self, checkpoint_path: str) -> None:
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(checkpoint["model_state_dict"])

    def _save_checkpoint(self, filename: str, epoch: int, metrics: Dict[str, float]) -> None:
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "metrics": metrics,
            "config": self.config.to_dict(),
        }
        torch.save(checkpoint, self.output_dir / "checkpoints" / filename)

    def _save_summary(self, summary: Dict[str, Any]) -> None:
        with (self.output_dir / "training_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)