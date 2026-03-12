"""把解析后的 KiCad 项目转换为 graph-text 检索样本。"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


class GraphTextPairBuilder:
    """构建第一阶段 graph-text retrieval 数据。"""

    def __init__(self, seed: int = 7, negatives_per_sample: int = 2) -> None:
        self.seed = seed
        self.negatives_per_sample = max(0, negatives_per_sample)

    def build_pairs(self, parsed_data_dir: str, output_dir: str) -> Dict[str, Any]:
        parsed_path = Path(parsed_data_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        project_files = sorted(parsed_path.glob("*.json"))
        if len(project_files) < 3:
            raise ValueError("graph-text 数据至少需要 3 个解析后的项目，用于 board-level 划分")

        split_projects = self._split_projects(project_files)
        random_gen = random.Random(self.seed)

        split_summaries: Dict[str, Dict[str, Any]] = {}
        for split_name, files in split_projects.items():
            projects = [self._load_project(path) for path in files]
            pool = self._build_negative_text_pool(projects)
            samples = self._build_split_samples(projects, pool, random_gen)
            self._save_split(output_path / split_name, split_name, samples)

            split_summaries[split_name] = {
                "num_boards": len(projects),
                "num_samples": len(samples),
            }

        summary = {
            "task_type": "GraphTextRetrieval",
            "num_projects": len(project_files),
            "negatives_per_sample": self.negatives_per_sample,
            "feature_schema": self.feature_schema(),
            "splits": split_summaries,
        }

        with (output_path / "dataset_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)

        return summary

    @staticmethod
    def feature_schema() -> List[str]:
        return [
            "num_components",
            "num_tracks",
            "num_vias",
            "num_nets",
            "num_layers",
            "avg_track_length",
            "avg_track_width",
            "avg_via_size",
            "power_net_ratio",
            "signal_net_ratio",
            "top_layer_track_ratio",
            "bottom_layer_track_ratio",
        ]

    def _split_projects(self, project_files: Sequence[Path]) -> Dict[str, List[Path]]:
        total = len(project_files)
        train_count = max(1, total - 2)
        val_count = 1
        test_count = total - train_count - val_count
        if test_count <= 0:
            raise ValueError("无法形成 train/val/test 三个 split")

        return {
            "train": list(project_files[:train_count]),
            "val": list(project_files[train_count : train_count + val_count]),
            "test": list(project_files[train_count + val_count :]),
        }

    def _load_project(self, project_path: Path) -> Dict[str, Any]:
        with project_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _build_split_samples(
        self,
        projects: Sequence[Dict[str, Any]],
        negative_text_pool: Sequence[str],
        random_gen: random.Random,
    ) -> List[Dict[str, Any]]:
        samples: List[Dict[str, Any]] = []
        sample_id = 0
        for project in projects:
            board_id = project["project_name"]
            graph_features = self._extract_graph_features(project)
            positives = self._build_positive_texts(project)

            for text in positives:
                sample = {
                    "sample_id": f"{board_id}_{sample_id}",
                    "task_type": "GraphTextRetrieval",
                    "board_id": board_id,
                    "text": text,
                    "graph_features": graph_features,
                    "hard_negatives": self._sample_negatives(
                        text,
                        negative_text_pool,
                        random_gen,
                        self.negatives_per_sample,
                    ),
                    "metadata": {
                        "source_project": board_id,
                        "text_type": self._guess_text_type(text),
                    },
                }
                sample_id += 1
                samples.append(sample)
        return samples

    def _build_negative_text_pool(self, projects: Sequence[Dict[str, Any]]) -> List[str]:
        pool: List[str] = []
        for project in projects:
            pool.extend(self._build_positive_texts(project))
        return pool

    def _sample_negatives(
        self,
        positive_text: str,
        pool: Sequence[str],
        random_gen: random.Random,
        count: int,
    ) -> List[str]:
        candidates = [text for text in pool if text != positive_text]
        if not candidates or count <= 0:
            return []
        if len(candidates) <= count:
            return list(candidates)
        return random_gen.sample(candidates, k=count)

    def _build_positive_texts(self, project: Dict[str, Any]) -> List[str]:
        board = project.get("board", {})
        board_id = project.get("project_name", "unknown_board")
        nets = board.get("nets", [])
        tracks = board.get("tracks", [])
        vias = board.get("vias", [])
        layers = board.get("layers", [])
        components = board.get("components", [])

        summary_text = (
            f"Board {board_id} has {len(components)} components, {len(nets)} nets, "
            f"{len(tracks)} tracks, {len(vias)} vias and {len(layers)} layers."
        )
        texts = [summary_text]

        named_nets = [str(net.get("name", "")).strip() for net in nets if str(net.get("name", "")).strip()]
        if named_nets:
            top_nets = ", ".join(named_nets[:4])
            texts.append(f"Key nets of board {board_id}: {top_nets}.")

        if tracks:
            avg_width = sum(float(track.get("width", 0.0)) for track in tracks) / len(tracks)
            texts.append(f"Board {board_id} average track width is about {avg_width:.3f} mm.")

        return texts

    def _extract_graph_features(self, project: Dict[str, Any]) -> List[float]:
        board = project.get("board", {})
        tracks = board.get("tracks", [])
        vias = board.get("vias", [])
        nets = board.get("nets", [])
        layers = board.get("layers", [])
        components = board.get("components", [])

        track_lengths = [self._track_length(track) for track in tracks]
        track_widths = [float(track.get("width", 0.0)) for track in tracks]
        via_sizes = [float(via.get("size", 0.0)) for via in vias]

        net_names = [str(net.get("name", "")).upper() for net in nets]
        power_nets = [name for name in net_names if any(tag in name for tag in ("GND", "VCC", "VDD", "VBAT", "3V3"))]
        signal_nets = [name for name in net_names if name and name not in power_nets]

        top_tracks = [track for track in tracks if str(track.get("layer", "")).upper() == "F.CU"]
        bottom_tracks = [track for track in tracks if str(track.get("layer", "")).upper() == "B.CU"]

        return [
            float(len(components)),
            float(len(tracks)),
            float(len(vias)),
            float(len(nets)),
            float(len(layers)),
            float(sum(track_lengths) / len(track_lengths)) if track_lengths else 0.0,
            float(sum(track_widths) / len(track_widths)) if track_widths else 0.0,
            float(sum(via_sizes) / len(via_sizes)) if via_sizes else 0.0,
            float(len(power_nets) / len(net_names)) if net_names else 0.0,
            float(len(signal_nets) / len(net_names)) if net_names else 0.0,
            float(len(top_tracks) / len(tracks)) if tracks else 0.0,
            float(len(bottom_tracks) / len(tracks)) if tracks else 0.0,
        ]

    def _track_length(self, track: Dict[str, Any]) -> float:
        start = track.get("start", [0.0, 0.0])
        end = track.get("end", [0.0, 0.0])
        if not isinstance(start, list) or not isinstance(end, list) or len(start) != 2 or len(end) != 2:
            return 0.0
        dx = float(end[0]) - float(start[0])
        dy = float(end[1]) - float(start[1])
        return float(math.sqrt(dx * dx + dy * dy))

    def _save_split(self, split_dir: Path, split_name: str, samples: Sequence[Dict[str, Any]]) -> None:
        split_dir.mkdir(parents=True, exist_ok=True)
        with (split_dir / "data.jsonl").open("w", encoding="utf-8") as handle:
            for sample in samples:
                json.dump(sample, handle, ensure_ascii=False)
                handle.write("\n")

        metadata = {
            "split": split_name,
            "task_type": "GraphTextRetrieval",
            "num_samples": len(samples),
            "feature_schema": self.feature_schema(),
        }
        with (split_dir / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, ensure_ascii=False)

    def _guess_text_type(self, text: str) -> str:
        lowered = text.lower()
        if "key nets" in lowered:
            return "net_description"
        if "average track width" in lowered:
            return "route_property"
        return "board_summary"
