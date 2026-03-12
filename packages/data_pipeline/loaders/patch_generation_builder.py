"""PatchGenerationLite 数据构建器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..transformers import PatchPromptSerializer


class PatchGenerationBuilder:
    """从解析后的 KiCad 板级 JSON 构建 patch 生成数据集。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_samples_per_board = int(self.config.get("max_samples_per_board", 64))
        self.serializer = PatchPromptSerializer(
            max_context_tracks=int(self.config.get("max_context_tracks", 16))
        )

    def build_dataset(self, parsed_data_dir: str, output_dir: str) -> Dict[str, Any]:
        parsed_path = Path(parsed_data_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        project_files = sorted(parsed_path.glob("*.json"))
        if not project_files:
            raise FileNotFoundError(f"在 {parsed_path} 中未找到解析后的项目文件")
        if len(project_files) < 3:
            raise ValueError("board-level 划分至少需要 3 个已解析板子")

        board_samples: Dict[Path, List[Dict[str, Any]]] = {}
        for project_file in project_files:
            with project_file.open("r", encoding="utf-8") as handle:
                project_data = json.load(handle)
            board_samples[project_file] = self._extract_samples(project_data)

        split_projects = self._split_projects(project_files, board_samples)
        summary: Dict[str, Any] = {
            "task_type": "PatchGenerationLite",
            "splits": {},
        }

        for split_name, files in split_projects.items():
            samples: List[Dict[str, Any]] = []
            board_ids: List[str] = []
            for project_file in files:
                with project_file.open("r", encoding="utf-8") as handle:
                    project_data = json.load(handle)
                board_id = project_data.get("project_name", project_file.stem)
                board_ids.append(board_id)
                samples.extend(board_samples[project_file])
            self._save_split(output_path / split_name, split_name, samples, board_ids)
            summary["splits"][split_name] = {
                "num_boards": len(board_ids),
                "num_samples": len(samples),
                "boards": board_ids,
            }

        with (output_path / "dataset_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
        return summary

    def _extract_samples(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        project_name = project_data.get("project_name", "unknown_project")
        board = project_data.get("board", {})
        tracks = [track for track in board.get("tracks", []) if track.get("type") == "segment"]
        vias = list(board.get("vias", []))
        nets = {net.get("id"): net.get("name", f"NET_{net.get('id')}") for net in board.get("nets", [])}

        samples: List[Dict[str, Any]] = []
        for index, track in enumerate(tracks[: self.max_samples_per_board]):
            net_id = track.get("net")
            net_name = nets.get(net_id, f"NET_{net_id}")
            patch = {
                "version": "v1",
                "op": "add_trace",
                "net_id": net_name,
                "params": {
                    "layer": track.get("layer", "F.Cu"),
                    "points": [track.get("start", [0.0, 0.0]), track.get("end", [0.0, 0.0])],
                    "width": track.get("width", 0.25),
                    "mode": "direct",
                },
            }
            context_text = self.serializer.serialize_track_context(
                project_name=project_name,
                board=board,
                focus_track=track,
                all_tracks=tracks,
            )
            samples.append(
                {
                    "task_type": "PatchGenerationLite",
                    "instruction": "根据上下文生成可执行 Patch DSL，恢复被遮蔽的线路段。",
                    "context_text": context_text,
                    "target_patch": json.dumps(patch, ensure_ascii=False, sort_keys=True),
                    "metadata": {
                        "project_name": project_name,
                        "board_id": project_name,
                        "source_type": "track_segment",
                        "source_index": index,
                        "net_id": net_name,
                        "op": "add_trace",
                    },
                }
            )

        remaining = max(0, self.max_samples_per_board - len(samples))
        for index, via in enumerate(vias[:remaining]):
            net_id = via.get("net")
            net_name = nets.get(net_id, f"NET_{net_id}")
            patch = {
                "version": "v1",
                "op": "add_via",
                "net_id": net_name,
                "params": {
                    "at": via.get("at", [0.0, 0.0]),
                    "layers": via.get("layers", ["F.Cu", "B.Cu"]),
                    "drill": via.get("drill", 0.3),
                },
            }
            context_text = self.serializer.serialize_via_context(
                project_name=project_name,
                board=board,
                focus_via=via,
                all_tracks=tracks,
            )
            samples.append(
                {
                    "task_type": "PatchGenerationLite",
                    "instruction": "根据上下文生成可执行 Patch DSL，补充正确的过孔操作。",
                    "context_text": context_text,
                    "target_patch": json.dumps(patch, ensure_ascii=False, sort_keys=True),
                    "metadata": {
                        "project_name": project_name,
                        "board_id": project_name,
                        "source_type": "via",
                        "source_index": index,
                        "net_id": net_name,
                        "op": "add_via",
                    },
                }
            )
        return samples

    def _split_projects(
        self,
        project_files: List[Path],
        board_samples: Dict[Path, List[Dict[str, Any]]],
    ) -> Dict[str, List[Path]]:
        ordered = sorted(project_files, key=lambda path: (len(board_samples[path]) > 0, str(path)))
        valid_boards = sum(1 for path in ordered if len(board_samples[path]) > 0)
        if valid_boards < 3:
            raise ValueError(f"至少需要 3 个有样本的板子，当前仅有 {valid_boards} 个")

        train_count = max(1, len(ordered) - 2)
        return {
            "train": ordered[:train_count],
            "val": ordered[train_count : train_count + 1],
            "test": ordered[train_count + 1 :],
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
            "task_type": "PatchGenerationLite",
            "num_samples": len(samples),
            "board_ids": board_ids,
        }
        with (split_dir / "metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, ensure_ascii=False)
