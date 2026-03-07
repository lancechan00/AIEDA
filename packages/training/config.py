"""最小训练配置。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


DEFAULT_DIRECTIONS = ["up", "down", "left", "right", "stop"]


@dataclass
class TrainingConfig:
    """第一阶段最小可运行配置。"""

    experiment_name: str = "local_route_choice_lite"
    task_type: str = "LocalRouteChoiceLite"
    dataset_path: str = "./data/fixtures/local_route_choice_lite"
    output_dir: str = "./outputs/local_route_choice_lite"

    model_name: str = "tiny_baseline"
    modalities: List[str] = field(default_factory=lambda: ["geometry", "image"])
    geometry_channels: int = 4
    image_channels: int = 3
    hidden_dim: int = 64
    num_classes: int = 5
    label_names: List[str] = field(default_factory=lambda: DEFAULT_DIRECTIONS.copy())

    batch_size: int = 2
    num_workers: int = 0
    epochs: int = 1
    learning_rate: float = 1e-3
    weight_decay: float = 0.0
    gradient_clip_norm: float = 1.0

    save_best_model: bool = True
    log_every_n_steps: int = 1
    seed: int = 7
    device: str = "auto"

    @classmethod
    def from_yaml(cls, config_path: str) -> "TrainingConfig":
        """从扁平 YAML 加载配置。"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}

        if not isinstance(raw, dict):
            raise ValueError("训练配置必须是字典格式")

        # 兼容旧版嵌套字段，但不再支持 `_base_`。
        if "_base_" in raw:
            raise ValueError("当前配置不再支持 `_base_` 继承，请改用扁平 YAML")

        flattened = cls._flatten_legacy_config(raw)
        return cls(**flattened)

    @staticmethod
    def _flatten_legacy_config(raw: Dict[str, Any]) -> Dict[str, Any]:
        """兼容旧版嵌套结构，统一拉平成最小配置。"""
        flattened = dict(raw)

        model = flattened.pop("model", None)
        if isinstance(model, dict):
            flattened.setdefault("model_name", model.get("name", model.get("model_name", "tiny_baseline")))
            flattened.setdefault("modalities", model.get("modalities", ["geometry", "image"]))
            flattened.setdefault("hidden_dim", model.get("hidden_dim", flattened.get("hidden_dim", 64)))
            flattened.setdefault("num_classes", model.get("num_classes", flattened.get("num_classes", 5)))

        data = flattened.pop("data", None)
        if isinstance(data, dict):
            flattened.setdefault("dataset_path", data.get("dataset_path", flattened.get("dataset_path")))
            flattened.setdefault("batch_size", data.get("batch_size", flattened.get("batch_size", 2)))
            flattened.setdefault("num_workers", data.get("num_workers", flattened.get("num_workers", 0)))

        optimizer = flattened.pop("optimizer", None)
        if isinstance(optimizer, dict):
            flattened.setdefault("learning_rate", optimizer.get("lr", flattened.get("learning_rate", 1e-3)))
            flattened.setdefault("weight_decay", optimizer.get("weight_decay", flattened.get("weight_decay", 0.0)))

        training = flattened.pop("training", None)
        if isinstance(training, dict):
            flattened.setdefault("epochs", training.get("epochs", flattened.get("epochs", 1)))
            flattened.setdefault(
                "gradient_clip_norm",
                training.get("gradient_clip_norm", flattened.get("gradient_clip_norm", 1.0)),
            )

        logging_cfg = flattened.pop("logging", None)
        if isinstance(logging_cfg, dict):
            flattened.setdefault(
                "log_every_n_steps",
                logging_cfg.get("log_every_n_steps", flattened.get("log_every_n_steps", 1)),
            )

        flattened.pop("scheduler", None)
        flattened.pop("evaluation", None)
        flattened.pop("checkpoint", None)
        return flattened

    def to_dict(self) -> Dict[str, Any]:
        """导出为普通字典。"""
        return asdict(self)

    def to_yaml(self, output_path: str) -> None:
        """保存配置。"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_dict(), handle, sort_keys=False, allow_unicode=True)

    def __post_init__(self) -> None:
        if self.task_type != "LocalRouteChoiceLite":
            raise ValueError("第一阶段当前只支持 `LocalRouteChoiceLite`")

        if not self.modalities:
            raise ValueError("`modalities` 不能为空")

        if self.num_classes != len(self.label_names):
            self.num_classes = len(self.label_names)