#!/usr/bin/env python3
"""合并 GraphTextRetrieval 多 seed 评估结果到单一 JSON 报告。"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="合并 embedding 多 seed 评估报告")
    parser.add_argument("--output", default="./outputs/embedding_multi_seed_report.json", help="输出路径")
    args = parser.parse_args()

    report: dict = {"task_type": "GraphTextRetrieval", "seeds": {}, "summary": {}}

    def _extract_json(raw: str) -> dict | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        start = raw.find("{")
        if start >= 0:
            depth, i = 0, start
            for i in range(start, len(raw)):
                if raw[i] == "{":
                    depth += 1
                elif raw[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw[start : i + 1])
                        except json.JSONDecodeError:
                            pass
                        break
        return None

    for eval_path in sorted(Path(p) for p in glob.glob("./outputs/embedding_eval_seed*_test.json")):
        seed = eval_path.stem.replace("embedding_eval_seed", "").replace("_test", "")
        try:
            with eval_path.open("r", encoding="utf-8-sig") as f:
                raw = f.read()
            metrics = _extract_json(raw)
            if metrics is not None:
                report["seeds"][seed] = {"test": metrics}
        except Exception as e:
            report["seeds"][seed] = {"test": {"error": str(e)}}

    for eval_path in sorted(Path(p) for p in glob.glob("./outputs/embedding_eval_seed*_noise005.json")):
        seed = eval_path.stem.replace("embedding_eval_seed", "").replace("_noise005", "")
        try:
            with eval_path.open("r", encoding="utf-8-sig") as f:
                raw = f.read()
            metrics = _extract_json(raw)
            if metrics is not None and seed in report["seeds"]:
                report["seeds"][seed]["test_noise005"] = metrics
        except Exception:
            pass

    if report["seeds"]:
        r1_values = []
        for s, data in report["seeds"].items():
            if "test" in data and "recall_at_1" in data["test"] and "error" not in data["test"]:
                r1_values.append(data["test"]["recall_at_1"])
        if r1_values:
            report["summary"]["recall_at_1_mean"] = sum(r1_values) / len(r1_values)
            report["summary"]["recall_at_1_min"] = min(r1_values)
            report["summary"]["recall_at_1_max"] = max(r1_values)
            report["summary"]["num_seeds"] = len(r1_values)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"已写入: {out_path}")


if __name__ == "__main__":
    main()
