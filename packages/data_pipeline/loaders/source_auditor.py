"""KiCad 数据源审计工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class KiCadSourceAuditor:
    """扫描目录并输出可采集项目清单。"""

    def audit(self, source_dir: str, output_file: str) -> Dict[str, object]:
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"source_dir 不存在: {source_path}")

        projects = self._discover_projects(source_path)
        output_path = Path(output_file)
        # 使用相对路径便于开源可移植；source_dir 相对于 manifest 所在目录
        try:
            source_dir_rel = str(source_path.relative_to(output_path.parent))
        except ValueError:
            source_dir_rel = "."
        summary = {
            "source_dir": source_dir_rel,
            "total_projects": len(projects),
            "projects": projects,
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)

        return summary

    def _discover_projects(self, source_path: Path) -> List[Dict[str, object]]:
        discovered: Dict[str, Dict[str, object]] = {}

        def _rel(p: Path) -> str:
            try:
                return str(p.relative_to(source_path))
            except ValueError:
                return p.name

        for pcb_file in source_path.rglob("*.kicad_pcb"):
            project_dir = pcb_file.parent
            key = _rel(project_dir)
            item = discovered.setdefault(
                key,
                {
                    "project_dir": key,
                    "project_name": project_dir.name,
                    "pcb_files": [],
                    "sch_files": [],
                    "net_files": [],
                },
            )
            item["pcb_files"].append(_rel(pcb_file))

        for sch_file in source_path.rglob("*.kicad_sch"):
            key = _rel(sch_file.parent)
            item = discovered.setdefault(
                key,
                {
                    "project_dir": key,
                    "project_name": sch_file.parent.name,
                    "pcb_files": [],
                    "sch_files": [],
                    "net_files": [],
                },
            )
            item["sch_files"].append(_rel(sch_file))

        for net_file in source_path.rglob("*.net"):
            key = _rel(net_file.parent)
            item = discovered.setdefault(
                key,
                {
                    "project_dir": key,
                    "project_name": net_file.parent.name,
                    "pcb_files": [],
                    "sch_files": [],
                    "net_files": [],
                },
            )
            item["net_files"].append(_rel(net_file))

        projects = []
        for project in discovered.values():
            if project["pcb_files"]:
                project["has_required_files"] = True
                projects.append(project)

        projects.sort(key=lambda item: str(item["project_name"]))
        return projects
