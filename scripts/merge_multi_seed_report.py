#!/usr/bin/env python3
"""合并审计与多 seed 评估结果到单一 JSON 报告。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    import argparse
    import glob

    parser = argparse.ArgumentParser(description="合并 multi-seed 审计与评估报告")
    parser.add_argument("--audit", default="./outputs/multi_seed_audit.json", help="审计 JSON 路径")
    parser.add_argument("--evals", nargs="*", help="eval 输出文件列表（可传入 glob 展开后的多个文件）")
    parser.add_argument("--output", default="./outputs/multi_seed_audit.json", help="合并后输出路径")
    args = parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"错误：审计文件不存在 {audit_path}")
        sys.exit(1)

    with audit_path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    report["multi_seed_test"] = {}
    eval_files = args.evals if args.evals else glob.glob("./outputs/eval_seed*.json")
    for eval_path in sorted(Path(p) for p in eval_files):
        if not eval_path.exists():
            continue
        try:
            with eval_path.open("r", encoding="utf-8") as f:
                raw = f.read().strip()
            metrics = json.loads(raw)
            seed = eval_path.stem.replace("eval_seed", "")
            report["multi_seed_test"][seed] = metrics
        except Exception as e:
            report["multi_seed_test"][str(eval_path)] = {"error": str(e)}

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"已写入: {out_path}")


if __name__ == "__main__":
    main()
