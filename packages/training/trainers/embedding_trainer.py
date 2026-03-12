"""Graph-text embedding 训练器。"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Union


def _rel_path_for_summary(path: Union[Path, str]) -> str:
    """将路径转为相对路径，便于开源可移植。"""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

from ...evaluation import compute_retrieval_metrics
from ...models import GraphFeatureEncoder, HashTextEncoder, QwenTextEncoder
from ..datasets import EmbeddingPairDatasetBuilder
from ..embedding_config import EmbeddingTrainingConfig

logger = logging.getLogger(__name__)


class EmbeddingTrainer:
    """训练 graph -> text 空间对齐。"""

    def __init__(self, config: EmbeddingTrainingConfig, output_dir: Optional[str] = None) -> None:
        self.config = config
        self.output_dir = Path(output_dir or config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

        self._set_seed(config.seed)
        self.device = self._setup_device()
        self.graph_encoder = GraphFeatureEncoder(
            input_dim=config.graph_feature_dim,
            hidden_dim=config.graph_hidden_dim,
            output_dim=config.embedding_dim,
        ).to(self.device)
        self.text_encoder, self.text_encoder_kind = self._setup_text_encoder()

        trainable_modules: List[nn.Module] = [self.graph_encoder]
        if not config.freeze_text_encoder and self.text_encoder_kind == "qwen":
            trainable_modules.append(self.text_encoder)
        self.optimizer = torch.optim.AdamW(
            self._trainable_parameters(trainable_modules),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

        self.best_recall_at_1 = float("-inf")
        self.history: List[Dict[str, Any]] = []

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

    def _setup_text_encoder(self) -> tuple[nn.Module, str]:
        mode = self.config.text_encoder_mode
        if mode == "hash":
            encoder = HashTextEncoder(output_dim=self.config.embedding_dim)
            return encoder.to(self.device), "hash"

        if mode == "qwen":
            encoder = QwenTextEncoder(model_name=self.config.text_model_name, max_length=self.config.max_text_length)
            encoder = encoder.to(self.device)
            return encoder, "qwen"

        try:
            encoder = QwenTextEncoder(model_name=self.config.text_model_name, max_length=self.config.max_text_length)
            encoder = encoder.to(self.device)
            logger.info("text encoder mode=auto, using qwen model: %s", self.config.text_model_name)
            return encoder, "qwen"
        except Exception as error:
            logger.warning("qwen 模型加载失败，退化到 hash 文本编码器: %s", error)
            encoder = HashTextEncoder(output_dim=self.config.embedding_dim)
            return encoder.to(self.device), "hash"

    def _trainable_parameters(self, modules: List[nn.Module]) -> List[nn.Parameter]:
        params: List[nn.Parameter] = []
        for module in modules:
            params.extend([param for param in module.parameters() if param.requires_grad])
        return params

    def _build_loader(self, split: str, shuffle: bool) -> torch.utils.data.DataLoader:
        dataset = EmbeddingPairDatasetBuilder.create_dataset(self.config.dataset_path, split=split)
        return EmbeddingPairDatasetBuilder.create_data_loader(
            dataset=dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=self.config.num_workers,
        )

    def _encode_texts(self, texts: List[str], training: bool) -> torch.Tensor:
        if self.text_encoder_kind == "hash":
            embeddings = self.text_encoder(texts).to(self.device)
            return embeddings.float()

        if training and self.config.freeze_text_encoder:
            with torch.no_grad():
                return self.text_encoder(texts).float()
        return self.text_encoder(texts).float()

    def _encode_hard_negatives(self, negatives: List[List[str]]) -> Optional[torch.Tensor]:
        first_negatives = [items[0] for items in negatives if items]
        if len(first_negatives) != len(negatives):
            return None
        negative_embeddings = self._encode_texts(first_negatives, training=True)
        return nn.functional.normalize(negative_embeddings, dim=-1)

    def _contrastive_loss(
        self,
        graph_embeddings: torch.Tensor,
        text_embeddings: torch.Tensor,
        hard_negative_embeddings: Optional[torch.Tensor],
    ) -> torch.Tensor:
        graph_norm = nn.functional.normalize(graph_embeddings, dim=-1)
        text_norm = nn.functional.normalize(text_embeddings, dim=-1)
        logits = torch.matmul(graph_norm, text_norm.T) / self.config.temperature

        labels = torch.arange(logits.shape[0], device=logits.device)
        loss_g2t = nn.functional.cross_entropy(logits, labels)
        loss_t2g = nn.functional.cross_entropy(logits.T, labels)
        loss = (loss_g2t + loss_t2g) * 0.5

        if hard_negative_embeddings is not None:
            positive_scores = torch.sum(graph_norm * text_norm, dim=-1)
            negative_scores = torch.sum(graph_norm * hard_negative_embeddings, dim=-1)
            margin_loss = torch.relu(self.config.hard_negative_margin + negative_scores - positive_scores).mean()
            loss = loss + margin_loss

        return loss

    def train(self) -> Dict[str, Any]:
        train_loader = self._build_loader("train", shuffle=True)
        val_loader = self._build_loader("val", shuffle=False)

        for epoch in range(1, self.config.epochs + 1):
            train_metrics = self._run_epoch(train_loader, training=True)
            val_metrics = self._run_epoch(val_loader, training=False)

            epoch_record = {"epoch": epoch, "train": train_metrics, "val": val_metrics}
            self.history.append(epoch_record)

            self._save_checkpoint("last_model.pt", epoch, val_metrics)
            if self.config.save_best_model and val_metrics["recall_at_1"] >= self.best_recall_at_1:
                self.best_recall_at_1 = val_metrics["recall_at_1"]
                self._save_checkpoint("best_model.pt", epoch, val_metrics)

            logger.info(
                "epoch=%s train_loss=%.4f val_recall@1=%.4f val_mrr=%.4f",
                epoch,
                train_metrics["loss"],
                val_metrics["recall_at_1"],
                val_metrics["mrr"],
            )

        summary = {
            "task_type": self.config.task_type,
            "text_encoder_kind": self.text_encoder_kind,
            "best_recall_at_1": self.best_recall_at_1,
            "history": self.history,
            "output_dir": _rel_path_for_summary(self.output_dir),
        }
        self._save_summary(summary)
        return summary

    def _run_epoch(self, loader: torch.utils.data.DataLoader, training: bool) -> Dict[str, float]:
        self.graph_encoder.train(training)
        if self.text_encoder_kind == "qwen":
            self.text_encoder.train(training and not self.config.freeze_text_encoder)

        losses: List[float] = []
        graph_batches: List[torch.Tensor] = []
        text_batches: List[torch.Tensor] = []

        for step, batch in enumerate(loader, start=1):
            graph_features = batch["graph_features"].to(self.device)
            texts = batch["texts"]
            negatives = batch["hard_negatives"]

            graph_embeddings = self.graph_encoder(graph_features)
            text_embeddings = self._encode_texts(texts, training=training)
            hard_negative_embeddings = self._encode_hard_negatives(negatives)

            loss = self._contrastive_loss(
                graph_embeddings=graph_embeddings,
                text_embeddings=text_embeddings,
                hard_negative_embeddings=hard_negative_embeddings,
            )

            if training:
                self.optimizer.zero_grad()
                loss.backward()
                if self.config.gradient_clip_norm > 0:
                    torch.nn.utils.clip_grad_norm_(self.graph_encoder.parameters(), self.config.gradient_clip_norm)
                self.optimizer.step()

            losses.append(float(loss.detach().cpu().item()))
            graph_batches.append(nn.functional.normalize(graph_embeddings.detach().cpu(), dim=-1))
            text_batches.append(nn.functional.normalize(text_embeddings.detach().cpu(), dim=-1))

            if training and step % self.config.log_every_n_steps == 0:
                logger.info("step=%s loss=%.4f", step, loss.item())

        graph_matrix = torch.cat(graph_batches, dim=0)
        text_matrix = torch.cat(text_batches, dim=0)
        similarity = torch.matmul(graph_matrix, text_matrix.T)
        metrics = compute_retrieval_metrics(similarity)
        metrics["loss"] = float(sum(losses) / max(len(losses), 1))
        return metrics

    def evaluate(
        self,
        split: str = "test",
        checkpoint_path: Optional[str] = None,
        noise_std: float = 0.0,
    ) -> Dict[str, float]:
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        loader = self._build_loader(split=split, shuffle=False)
        return self._evaluate_loader(loader=loader, noise_std=noise_std)

    def _evaluate_loader(self, loader: torch.utils.data.DataLoader, noise_std: float) -> Dict[str, float]:
        self.graph_encoder.eval()
        if self.text_encoder_kind == "qwen":
            self.text_encoder.eval()

        graph_batches: List[torch.Tensor] = []
        text_batches: List[torch.Tensor] = []
        losses: List[float] = []

        with torch.no_grad():
            for batch in loader:
                graph_features = batch["graph_features"].to(self.device)
                if noise_std > 0:
                    graph_features = graph_features + torch.randn_like(graph_features) * noise_std
                texts = batch["texts"]
                negatives = batch["hard_negatives"]

                graph_embeddings = self.graph_encoder(graph_features)
                text_embeddings = self._encode_texts(texts, training=False)
                hard_negative_embeddings = self._encode_hard_negatives(negatives)
                loss = self._contrastive_loss(
                    graph_embeddings=graph_embeddings,
                    text_embeddings=text_embeddings,
                    hard_negative_embeddings=hard_negative_embeddings,
                )
                losses.append(float(loss.detach().cpu().item()))
                graph_batches.append(nn.functional.normalize(graph_embeddings.detach().cpu(), dim=-1))
                text_batches.append(nn.functional.normalize(text_embeddings.detach().cpu(), dim=-1))

        similarity = torch.matmul(torch.cat(graph_batches, dim=0), torch.cat(text_batches, dim=0).T)
        metrics = compute_retrieval_metrics(similarity)
        metrics["loss"] = float(sum(losses) / max(len(losses), 1))
        metrics["noise_std"] = float(noise_std)
        return metrics

    def load_checkpoint(self, checkpoint_path: str) -> None:
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.graph_encoder.load_state_dict(checkpoint["graph_encoder_state_dict"])

    def _save_checkpoint(self, filename: str, epoch: int, metrics: Dict[str, float]) -> None:
        checkpoint = {
            "epoch": epoch,
            "graph_encoder_state_dict": self.graph_encoder.state_dict(),
            "metrics": metrics,
            "config": self.config.to_dict(),
            "text_encoder_kind": self.text_encoder_kind,
        }
        torch.save(checkpoint, self.output_dir / "checkpoints" / filename)

    def _save_summary(self, summary: Dict[str, Any]) -> None:
        with (self.output_dir / "training_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
