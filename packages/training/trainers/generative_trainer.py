"""PatchGenerationLite 生成训练器。"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from torch.utils.data import DataLoader

from ...evaluation import compute_patch_metrics
from ...models import PcbMultimodalAdapter, get_backend
from ..datasets import PatchGenerationDatasetBuilder
from ..generative_config import GenerativeTrainingConfig

logger = logging.getLogger(__name__)


def _rel_path_for_summary(path: Union[Path, str]) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


class GenerativeTrainer:
    """最小监督生成训练器。"""

    def __init__(self, config: GenerativeTrainingConfig, output_dir: Optional[str] = None) -> None:
        self.config = config
        self.output_dir = Path(output_dir or config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

        self._set_seed(config.seed)
        self.device = self._setup_device()
        self.model = self._setup_model().to(self.device)
        self.tokenizer = self.model.tokenizer
        self.pcb_adapter = PcbMultimodalAdapter()
        self.optimizer = torch.optim.AdamW(
            self.model.get_trainable_params(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.best_exact_match = float("-inf")
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

    def _setup_model(self) -> torch.nn.Module:
        backend_cls = get_backend(self.config.model_name)
        model = backend_cls(
            task_type=self.config.task_type,
            text_model_name=self.config.text_model_name,
            load_pretrained=self.config.load_pretrained,
            local_files_only=self.config.local_files_only,
        )
        if getattr(model, "supports_training", True) is False:
            raise ValueError(f"{self.config.model_name} 当前不支持训练")
        return model

    def _build_loader(self, split: str, shuffle: bool) -> DataLoader:
        dataset = PatchGenerationDatasetBuilder.create_dataset(self.config.dataset_path, split=split)
        return PatchGenerationDatasetBuilder.create_data_loader(
            dataset=dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=self.config.num_workers,
        )

    def _build_train_batch(self, batch: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        max_total = self.config.max_input_length + self.config.max_target_length
        eos_token_id = self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else 1
        pad_token_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else eos_token_id

        input_rows: List[List[int]] = []
        label_rows: List[List[int]] = []
        prompt_rows: List[List[int]] = []

        for instruction, context_text, target_patch in zip(
            batch["instruction"], batch["context_text"], batch["target_patch"]
        ):
            pair = self.pcb_adapter.format_training_pair(instruction, context_text, target_patch)
            prompt_text = pair["prompt"]
            prompt_ids = self.tokenizer.encode(prompt_text, add_special_tokens=False)
            target_ids = self.tokenizer.encode(pair["target"], add_special_tokens=False)

            # 先截断 prompt，保证 target 一定进入序列，避免 labels 全为 -100 导致 NaN
            prompt_ids = prompt_ids[: self.config.max_input_length]
            target_ids = target_ids[: self.config.max_target_length]
            full_ids = prompt_ids + target_ids + [eos_token_id]
            labels = [-100] * len(prompt_ids) + target_ids + [eos_token_id]
            if len(full_ids) > max_total:
                full_ids = full_ids[:max_total]
                labels = labels[:max_total]
            if len(labels) < len(full_ids):
                labels += [-100] * (len(full_ids) - len(labels))

            input_rows.append(full_ids)
            label_rows.append(labels)
            prompt_rows.append(prompt_ids)

        max_len = max((len(row) for row in input_rows), default=1)
        padded_input = []
        padded_mask = []
        padded_labels = []
        for input_ids, labels in zip(input_rows, label_rows):
            pad_len = max_len - len(input_ids)
            padded_input.append(input_ids + [pad_token_id] * pad_len)
            padded_mask.append([1] * len(input_ids) + [0] * pad_len)
            padded_labels.append(labels + [-100] * pad_len)

        prompt_enc = self.tokenizer(
            [
                self.pcb_adapter.format_prompt(instruction=i, context_text=c)
                for i, c in zip(batch["instruction"], batch["context_text"])
            ],
            truncation=True,
            max_length=self.config.max_input_length,
            padding=True,
            return_tensors="pt",
            add_special_tokens=False,
        )

        return {
            "input_ids": torch.tensor(padded_input, dtype=torch.long, device=self.device),
            "attention_mask": torch.tensor(padded_mask, dtype=torch.long, device=self.device),
            "labels": torch.tensor(padded_labels, dtype=torch.long, device=self.device),
            "prompt_input_ids": prompt_enc["input_ids"].to(self.device),
            "prompt_attention_mask": prompt_enc["attention_mask"].to(self.device),
        }

    def train(self) -> Dict[str, Any]:
        train_loader = self._build_loader("train", shuffle=True)
        val_loader = self._build_loader("val", shuffle=False)

        for epoch in range(1, self.config.epochs + 1):
            train_metrics = self._run_epoch(train_loader, training=True)
            val_metrics = self._run_epoch(val_loader, training=False)
            self.history.append({"epoch": epoch, "train": train_metrics, "val": val_metrics})

            logger.info(
                "epoch=%s train_loss=%.4f val_loss=%.4f val_exact_match=%.4f",
                epoch,
                train_metrics["loss"],
                val_metrics["loss"],
                val_metrics.get("action_exact_match", 0.0),
            )
            self._save_checkpoint("last_model.pt", epoch, val_metrics)
            if self.config.save_best_model and val_metrics.get("action_exact_match", 0.0) >= self.best_exact_match:
                self.best_exact_match = val_metrics.get("action_exact_match", 0.0)
                self._save_checkpoint("best_model.pt", epoch, val_metrics)

        summary = {
            "history": self.history,
            "best_action_exact_match": self.best_exact_match,
            "output_dir": _rel_path_for_summary(self.output_dir),
        }
        self._save_summary(summary)
        return summary

    def _run_epoch(self, loader: DataLoader, training: bool) -> Dict[str, float]:
        self.model.train(training)
        running_loss = 0.0
        step_count = 0

        predictions: List[str] = []
        targets: List[str] = []
        generation_budget = self.config.eval_generation_samples if not training else 0

        for step, batch in enumerate(loader, start=1):
            model_inputs = self._build_train_batch(batch)
            outputs = self.model(
                input_ids=model_inputs["input_ids"],
                attention_mask=model_inputs["attention_mask"],
                labels=model_inputs["labels"],
            )
            loss = outputs["loss"] if "loss" in outputs else torch.tensor(0.0, device=self.device)

            if training and torch.isfinite(loss).all():
                self.optimizer.zero_grad()
                loss.backward()
                if self.config.gradient_clip_norm > 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip_norm)
                self.optimizer.step()
            elif training and not torch.isfinite(loss).all():
                logger.warning("step=%s loss=nan/inf 跳过 backward", step)

            running_loss += float(loss.item()) if torch.isfinite(loss).all() else 0.0
            step_count += 1

            if training and step % self.config.log_every_n_steps == 0:
                logger.info("step=%s loss=%.4f", step, loss.item())

            if generation_budget > 0:
                batch_predictions = self._generate_batch(
                    prompt_input_ids=model_inputs["prompt_input_ids"],
                    prompt_attention_mask=model_inputs["prompt_attention_mask"],
                )
                batch_targets = batch["target_patch"]
                take_n = min(generation_budget, len(batch_predictions))
                predictions.extend(batch_predictions[:take_n])
                targets.extend(batch_targets[:take_n])
                generation_budget -= take_n

        metrics: Dict[str, float] = {"loss": running_loss / max(step_count, 1)}
        if predictions:
            metrics.update(compute_patch_metrics(predictions=predictions, targets=targets))
        else:
            metrics.update(
                {
                    "parse_success_rate": 0.0,
                    "field_completeness_rate": 0.0,
                    "action_exact_match": 0.0,
                }
            )
        return metrics

    def _generate_batch(self, prompt_input_ids: torch.Tensor, prompt_attention_mask: torch.Tensor) -> List[str]:
        self.model.eval()
        with torch.no_grad():
            generated = self.model.generate(
                input_ids=prompt_input_ids,
                attention_mask=prompt_attention_mask,
                max_new_tokens=self.config.generation_max_new_tokens,
            )

        texts: List[str]
        if hasattr(self.tokenizer, "batch_decode"):
            texts = self.tokenizer.batch_decode(generated.tolist(), skip_special_tokens=True)
        else:
            texts = [self.tokenizer.decode(row, skip_special_tokens=True) for row in generated.tolist()]

        prompts = self.tokenizer.batch_decode(prompt_input_ids.tolist(), skip_special_tokens=True)
        cleaned = []
        for full_text, prompt_text in zip(texts, prompts):
            if full_text.startswith(prompt_text):
                cleaned.append(full_text[len(prompt_text) :].strip())
            else:
                cleaned.append(full_text.strip())
        return cleaned

    def evaluate(self, split: str = "test", checkpoint_path: Optional[str] = None) -> Dict[str, float]:
        if checkpoint_path:
            self.load_checkpoint(checkpoint_path)
        loader = self._build_loader(split=split, shuffle=False)
        return self._run_epoch(loader, training=False)

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
