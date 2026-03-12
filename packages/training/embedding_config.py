"""Qwen embedding 训练配置。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class EmbeddingTrainingConfig:
    experiment_name: str = "qwen3_embedding_graph_text"
    task_type: str = "GraphTextRetrieval"
    dataset_path: str = "./data/embedding/graph_text_pairs"
    output_dir: str = "./outputs/qwen3_embedding_graph_text"

    text_model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    text_encoder_mode: str = "auto"
    freeze_text_encoder: bool = True
    max_text_length: int = 256

    graph_feature_dim: int = 12
    graph_hidden_dim: int = 128
    embedding_dim: int = 1024
    temperature: float = 0.07
    hard_negative_margin: float = 0.1

    batch_size: int = 8
    num_workers: int = 0
    epochs: int = 3
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    gradient_clip_norm: float = 1.0

    save_best_model: bool = True
    log_every_n_steps: int = 10
    seed: int = 7
    device: str = "auto"

    @classmethod
    def from_yaml(cls, config_path: str) -> "EmbeddingTrainingConfig":
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        if not isinstance(raw, dict):
            raise ValueError("embedding 配置必须是字典格式")
        return cls(**raw)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_yaml(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_dict(), handle, sort_keys=False, allow_unicode=True)

    def __post_init__(self) -> None:
        if self.task_type != "GraphTextRetrieval":
            raise ValueError("embedding 训练当前只支持 `GraphTextRetrieval`")
        if self.text_encoder_mode not in {"auto", "qwen", "hash"}:
            raise ValueError("`text_encoder_mode` 仅支持 auto/qwen/hash")
        if self.embedding_dim <= 0:
            raise ValueError("`embedding_dim` 必须为正数")
