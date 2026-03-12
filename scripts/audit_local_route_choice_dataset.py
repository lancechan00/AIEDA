#!/usr/bin/env python3
"""审计 LocalRouteChoice-Lite 数据集：标签分布、类别平衡、split 统计。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.training.datasets.pcb_dataset import PCBDatasetBuilder


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="审计 LocalRouteChoice-Lite 数据集")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data/local_route_choice_lite_github",
        help="数据集目录",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 JSON 文件（可选）",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"错误：目录不存在 {data_dir}")
        sys.exit(1)

    result: dict = {"data_dir": str(data_dir), "splits": {}}
    label_names = ["up", "down", "left", "right", "stop"]

    for split in ["train", "val", "test"]:
        try:
            dataset = PCBDatasetBuilder.create_dataset(str(data_dir), split=split)
            stats = dataset.get_statistics()
        except FileNotFoundError as e:
            result["splits"][split] = {"error": str(e)}
            continue

        dist = stats["label_distribution"]
        total = stats["num_samples"]
        dist_pct = {k: round(v / total * 100, 1) for k, v in dist.items()} if total else {}

        result["splits"][split] = {
            "num_samples": total,
            "label_counts": dist,
            "label_percentages": dist_pct,
            "labels_missing": [lbl for lbl in label_names if lbl not in dist],
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n已写入: {out_path}")


if __name__ == "__main__":
    main()
