"""Graph-text retrieval 数据集。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset


class EmbeddingPairDatasetConfig:
    def __init__(self, data_dir: str, split: str = "train") -> None:
        self.data_dir = Path(data_dir)
        self.split = split


class EmbeddingPairDataset(Dataset):
    """读取 graph-text pair 数据集。"""

    def __init__(self, config: EmbeddingPairDatasetConfig):
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

        if not self.samples:
            raise ValueError(f"{data_file} 中没有有效样本")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = self.samples[idx]
        features = np.asarray(sample["graph_features"], dtype=np.float32)
        return {
            "sample_id": sample.get("sample_id", f"{self.config.split}_{idx}"),
            "board_id": sample.get("board_id", "unknown"),
            "graph_features": torch.from_numpy(features),
            "text": sample["text"],
            "hard_negatives": sample.get("hard_negatives", []),
            "metadata": sample.get("metadata", {}),
        }


class EmbeddingPairDatasetBuilder:
    @staticmethod
    def create_dataset(data_dir: str, split: str = "train") -> EmbeddingPairDataset:
        return EmbeddingPairDataset(EmbeddingPairDatasetConfig(data_dir=data_dir, split=split))

    @staticmethod
    def create_data_loader(
        dataset: EmbeddingPairDataset,
        batch_size: int = 8,
        shuffle: bool = True,
        num_workers: int = 0,
    ) -> DataLoader:
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=EmbeddingPairDatasetBuilder._collate_fn,
        )

    @staticmethod
    def _collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "sample_ids": [item["sample_id"] for item in batch],
            "board_ids": [item["board_id"] for item in batch],
            "graph_features": torch.stack([item["graph_features"] for item in batch]),
            "texts": [item["text"] for item in batch],
            "hard_negatives": [item["hard_negatives"] for item in batch],
            "metadata": [item["metadata"] for item in batch],
        }
