#!/usr/bin/env python3
"""根据 discovery manifest 下载 GitHub KiCad 仓库到 raw 数据目录。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List


def sanitize_name(value: str) -> str:
    safe = value.replace("/", "__").replace("\\", "__").replace(" ", "_")
    keep = []
    for ch in safe:
        if ch.isalnum() or ch in {"_", "-", "."}:
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def read_manifest(manifest_path: str) -> Dict[str, object]:
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"manifest 不存在: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("manifest 格式错误，应为 JSON 对象")
    return payload


def clone_repository(repo_url: str, default_branch: str, target_dir: Path, max_retries: int = 3) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    command_candidates = [
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--branch",
            default_branch,
            repo_url,
            str(target_dir),
        ],
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            default_branch,
            repo_url,
            str(target_dir),
        ],
    ]

    last_error: Exception | None = None
    for command in command_candidates:
        for attempt in range(max_retries):
            try:
                subprocess.run(command, check=True)
                return
            except subprocess.CalledProcessError as error:
                last_error = error
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"clone failed: {repo_url}")


def should_skip_project_dir(project_dir: Path, repo_dir: Path, excluded_keywords: List[str]) -> bool:
    relative_parts = [part.lower() for part in project_dir.relative_to(repo_dir).parts]
    return any(keyword in part for part in relative_parts for keyword in excluded_keywords)


def collect_kicad_projects(
    repo_dir: Path,
    output_root: Path,
    repo_key: str,
    excluded_keywords: List[str],
) -> List[str]:
    projects: List[str] = []
    for pcb_file in repo_dir.rglob("*.kicad_pcb"):
        project_dir = pcb_file.parent
        if should_skip_project_dir(project_dir=project_dir, repo_dir=repo_dir, excluded_keywords=excluded_keywords):
            continue
        relative_dir = project_dir.relative_to(repo_dir)
        project_name = sanitize_name(f"{repo_key}__{relative_dir}")
        target_project_dir = output_root / project_name
        target_project_dir.mkdir(parents=True, exist_ok=True)

        for source_file in project_dir.iterdir():
            if source_file.is_file() and source_file.suffix.lower() in {".kicad_pcb", ".kicad_sch", ".net"}:
                shutil.copy2(source_file, target_project_dir / source_file.name)

        projects.append(str(target_project_dir))
    return projects


def download_from_manifest(
    manifest_path: str,
    output_dir: str,
    limit: int,
    excluded_keywords: List[str],
) -> Dict[str, object]:
    payload = read_manifest(manifest_path)
    included = payload.get("included_repositories", [])
    if not isinstance(included, list):
        raise ValueError("manifest 中 included_repositories 格式错误")

    selected = included[:limit] if limit > 0 else included
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    records = []
    total_projects = 0
    for repo in selected:
        if not isinstance(repo, dict):
            continue
        full_name = str(repo.get("full_name", ""))
        html_url = str(repo.get("html_url", ""))
        default_branch = str(repo.get("default_branch", "main"))
        repo_key = sanitize_name(full_name)
        if not full_name or not html_url:
            continue

        with tempfile.TemporaryDirectory(prefix="aieda_repo_") as tmp:
            clone_dir = Path(tmp) / repo_key
            clone_repository(repo_url=html_url, default_branch=default_branch, target_dir=clone_dir)
            projects = collect_kicad_projects(
                repo_dir=clone_dir,
                output_root=output_root,
                repo_key=repo_key,
                excluded_keywords=excluded_keywords,
            )

        total_projects += len(projects)
        # 使用相对路径便于开源可移植；project dirs 相对于 output_root
        def _rel_to(p: str, base: Path) -> str:
            try:
                return str(Path(p).resolve().relative_to(base.resolve()))
            except ValueError:
                return Path(p).name

        project_rels = [_rel_to(p, output_root) for p in projects]
        records.append(
            {
                "full_name": full_name,
                "html_url": html_url,
                "default_branch": default_branch,
                "downloaded_project_dirs": project_rels,
                "num_projects": len(projects),
            }
        )

    # 使用相对路径便于开源可移植
    out_resolved = Path(output_dir).resolve()
    try:
        manifest_rel = str(Path(manifest_path).resolve().relative_to(out_resolved))
    except ValueError:
        manifest_rel = Path(manifest_path).name

    result = {
        "manifest": manifest_rel,
        "output_dir": ".",
        "excluded_path_keywords": excluded_keywords,
        "selected_repositories": len(records),
        "downloaded_projects": total_projects,
        "repositories": records,
    }

    summary_file = output_root / "download_summary.json"
    with summary_file.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 whitelist manifest 下载 KiCad 项目")
    parser.add_argument("--manifest", required=True, help="discovery 生成的 manifest")
    parser.add_argument("--output-dir", required=True, help="raw 数据输出目录")
    parser.add_argument("--limit", type=int, default=30, help="最多下载仓库数，0 表示全部")
    parser.add_argument(
        "--exclude-path-keywords",
        default="test,tests,docs,.github,fixture,fixtures",
        help="路径包含这些关键词时跳过该项目目录，逗号分隔",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    excluded_keywords = [item.strip().lower() for item in args.exclude_path_keywords.split(",") if item.strip()]
    result = download_from_manifest(
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        limit=args.limit,
        excluded_keywords=excluded_keywords,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
