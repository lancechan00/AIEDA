"""PatchGenerationLite 数据集。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from torch.utils.data import DataLoader, Dataset


class PatchGenerationDatasetConfig:
    def __init__(self, data_dir: str, split: str = "train") -> None:
        self.data_dir = Path(data_dir)
        self.split = split


class PatchGenerationDataset(Dataset):
    """读取 patch 生成数据样本。"""

    def __init__(self, config: PatchGenerationDatasetConfig):
        self.config = config
        self.samples: List[Dict[str, Any]] = []
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

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        sample = self.samples[index]
        return {
            "instruction": sample.get("instruction", ""),
            "context_text": sample.get("context_text", ""),
            "target_patch": sample.get("target_patch", ""),
            "metadata": sample.get("metadata", {}),
        }


class PatchGenerationDatasetBuilder:
    @staticmethod
    def create_dataset(data_dir: str, split: str = "train") -> PatchGenerationDataset:
        return PatchGenerationDataset(PatchGenerationDatasetConfig(data_dir=data_dir, split=split))

    @staticmethod
    def create_data_loader(
        dataset: PatchGenerationDataset,
        batch_size: int = 2,
        shuffle: bool = True,
        num_workers: int = 0,
    ) -> DataLoader:
        return DataLoader(
            dataset=dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=PatchGenerationDatasetBuilder._collate_fn,
        )

    @staticmethod
    def _collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "instruction": [sample["instruction"] for sample in batch],
            "context_text": [sample["context_text"] for sample in batch],
            "target_patch": [sample["target_patch"] for sample in batch],
            "metadata": [sample["metadata"] for sample in batch],
        }
