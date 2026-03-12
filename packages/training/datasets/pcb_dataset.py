"""最小 PCB 数据集。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)

LABEL_TO_INDEX = {"up": 0, "down": 1, "left": 2, "right": 3, "stop": 4}


class PCBDatasetConfig:
    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.split = split
        self.transform = transform


class PCBDataset(Dataset):
    """读取 `data.jsonl` 中的样本。"""

    def __init__(self, config: PCBDatasetConfig):
        self.config = config
        self.samples: List[Dict[str, Any]] = []
        self.task_type = "LocalRouteChoiceLite"
        self._load_data()

    def _load_data(self) -> None:
        data_file = self.config.data_dir / self.config.split / "data.jsonl"
        if not data_file.exists():
            raise FileNotFoundError(f"数据文件不存在: {data_file}")

        with data_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    self.samples.append(json.loads(line))

        if not self.samples:
            logger.warning("%s 无样本，将返回空数据集", data_file)
            self.task_type = "LocalRouteChoiceLite"
        else:
            self.task_type = self.samples[0].get("task_type", "LocalRouteChoiceLite")
        logger.info("加载 %s split: %s 条样本", self.config.split, len(self.samples))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = dict(self.samples[idx])

        geometry = np.asarray(sample["geometry"], dtype=np.float32)
        image = np.asarray(sample["image"], dtype=np.float32) / 255.0

        sample["geometry"] = torch.from_numpy(np.transpose(geometry, (2, 0, 1)))
        sample["image"] = torch.from_numpy(np.transpose(image, (2, 0, 1)))
        sample["label"] = torch.tensor(self._label_to_index(sample["label"]), dtype=torch.long)

        if self.config.transform is not None:
            sample = self.config.transform(sample)

        return sample

    def _label_to_index(self, raw_label: Any) -> int:
        if isinstance(raw_label, int):
            return raw_label
        if isinstance(raw_label, dict):
            raw_label = raw_label.get("direction", "stop")
        if raw_label not in LABEL_TO_INDEX:
            raise ValueError(f"未知标签: {raw_label}")
        return LABEL_TO_INDEX[raw_label]

    def get_statistics(self) -> Dict[str, Any]:
        label_counts: Dict[str, int] = {}
        for sample in self.samples:
            label = sample["label"] if isinstance(sample["label"], str) else sample["label"]["direction"]
            label_counts[label] = label_counts.get(label, 0) + 1
        return {
            "task_type": self.task_type,
            "num_samples": len(self.samples),
            "label_distribution": label_counts,
        }


class PCBDatasetBuilder:
    @staticmethod
    def create_dataset(
        data_dir: str,
        split: str = "train",
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> PCBDataset:
        return PCBDataset(PCBDatasetConfig(data_dir=data_dir, split=split, transform=transform))

    @staticmethod
    def create_data_loader(
        dataset: PCBDataset,
        batch_size: int = 32,
        shuffle: bool = True,
        num_workers: int = 0,
    ) -> DataLoader:
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=PCBDatasetBuilder._collate_fn,
        )

    @staticmethod
    def _collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "geometry": torch.stack([sample["geometry"] for sample in batch]),
            "image": torch.stack([sample["image"] for sample in batch]),
            "label": torch.stack([sample["label"] for sample in batch]),
            "metadata": [sample.get("metadata", {}) for sample in batch],
        }