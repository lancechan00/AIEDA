"""Patch 生成训练配置。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class GenerativeTrainingConfig:
    experiment_name: str = "patch_generation_lite"
    task_type: str = "PatchGenerationLite"
    dataset_path: str = "./data/patch_generation_lite"
    output_dir: str = "./outputs/patch_generation_lite"

    model_name: str = "qwen_instruct"
    text_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
    load_pretrained: bool = False
    local_files_only: bool = True
    max_input_length: int = 1024
    max_target_length: int = 256
    generation_max_new_tokens: int = 192
    eval_generation_samples: int = 16

    batch_size: int = 2
    num_workers: int = 0
    epochs: int = 1
    learning_rate: float = 5e-5
    weight_decay: float = 0.0
    gradient_clip_norm: float = 1.0

    save_best_model: bool = True
    log_every_n_steps: int = 10
    seed: int = 7
    device: str = "auto"

    @classmethod
    def from_yaml(cls, config_path: str) -> "GenerativeTrainingConfig":
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        if not isinstance(raw, dict):
            raise ValueError("生成训练配置必须是字典格式")
        return cls(**raw)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_yaml(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_dict(), handle, sort_keys=False, allow_unicode=True)

    def __post_init__(self) -> None:
        if self.task_type != "PatchGenerationLite":
            raise ValueError("生成训练当前只支持 `PatchGenerationLite`")
        if self.max_input_length <= 0:
            raise ValueError("`max_input_length` 必须为正数")
        if self.max_target_length <= 0:
            raise ValueError("`max_target_length` 必须为正数")
        if self.eval_generation_samples < 0:
            raise ValueError("`eval_generation_samples` 不能为负数")
