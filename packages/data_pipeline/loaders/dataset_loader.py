"""第一阶段数据集构建器。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..transformers.sample_extractor import SampleExtractor

logger = logging.getLogger(__name__)


class DatasetLoader:
    """按 board-level 划分数据。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sample_extractor = SampleExtractor()

    def build_dataset(self, parsed_data_dir: str, output_dir: str, task_type: str) -> Dict[str, Any]:
        if task_type != "LocalRouteChoiceLite":
            raise ValueError("第一阶段当前只支持 `LocalRouteChoiceLite`")

        parsed_path = Path(parsed_data_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        project_files = sorted(parsed_path.glob("*.json"))
        if not project_files:
            raise FileNotFoundError(f"在 {parsed_path} 中未找到解析后的项目文件")

        split_projects = self._split_projects(project_files)
        summary = {"task_type": task_type, "splits": {}}

        for split_name, files in split_projects.items():
            split_samples: List[Dict[str, Any]] = []
            board_ids: List[str] = []
            for project_file in files:
                with project_file.open("r", encoding="utf-8") as handle:
                    project_data = json.load(handle)
                split_samples.extend(self.sample_extractor.extract_samples_from_project(project_data, task_type))
                board_ids.append(project_data["project_name"])

            self._save_split(output_path / split_name, split_name, split_samples, board_ids)
            summary["splits"][split_name] = {
                "boards": board_ids,
                "num_boards": len(board_ids),
                "num_samples": len(split_samples),
            }

        with (output_path / "dataset_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)

        return summary

    def _split_projects(self, project_files: List[Path]) -> Dict[str, List[Path]]:
        total = len(project_files)
        if total < 3:
            raise ValueError("board-level 划分至少需要 3 个已解析板子")

        train_count = max(1, total - 2)
        val_count = 1
        test_count = total - train_count - val_count
        if test_count <= 0:
            raise ValueError("无法形成 train/val/test 三个 board-level 划分")

        return {
            "train": project_files[:train_count],
            "val": project_files[train_count : train_count + val_count],
            "test": project_files[train_count + val_count : train_count + val_count + test_count],
        }

    def _save_split(
        self,
        split_dir: Path,
        split_name: str,
        samples: List[Dict[str, Any]],
        board_ids: List[str],
    ) -> None:
        split_dir.mkdir(parents=True, exist_ok=True)

        with (split_dir / "data.jsonl").open("w", encoding="utf-8") as handle:
            for sample in samples:
                json.dump(sample, handle, ensure_ascii=False)
                handle.write("\n")

        metadata = {
            "split": split_name,
            "task_type": "LocalRouteChoiceLite",
            "num_samples": len(samples),
            "board_ids": board_ids,
        }
        with (split_dir / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, ensure_ascii=False)

    def load_dataset(self, data_dir: str, split: str = "train") -> List[Dict[str, Any]]:
        data_file = Path(data_dir) / split / "data.jsonl"
        if not data_file.exists():
            raise FileNotFoundError(f"数据文件不存在: {data_file}")

        samples = []
        with data_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples

    def validate_dataset(self, data_dir: str) -> Dict[str, Any]:
        result = {"splits": {}, "valid": True}
        seen_boards = set()

        for split in ["train", "val", "test"]:
            samples = self.load_dataset(data_dir, split)
            board_ids = {sample["metadata"]["board_id"] for sample in samples}
            overlap = sorted(board_ids & seen_boards)
            seen_boards.update(board_ids)

            split_result = {
                "num_samples": len(samples),
                "num_boards": len(board_ids),
                "labels": sorted({sample["label"] for sample in samples}),
                "board_overlap_with_previous_splits": overlap,
            }
            result["splits"][split] = split_result
            if not samples or overlap:
                result["valid"] = False

        return result
