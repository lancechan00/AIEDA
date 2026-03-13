#!/usr/bin/env python3
"""Stage 2 PoC：使用 Qwen3-VL-Embedding-2B 做 image-text 检索，与 graph-text 基线对比。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _load_embedder():
    """动态加载 Qwen3VLEmbedder，需 transformers>=4.57 与 qwen-vl-utils。"""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError("请安装 huggingface_hub: pip install huggingface_hub") from None

    # 兼容 transformers 版本差异：部分版本无 check_model_inputs
    import transformers.utils.generic as _tf_generic
    if not hasattr(_tf_generic, "check_model_inputs"):
        _tf_generic.check_model_inputs = lambda f: f  # no-op

    script_path = hf_hub_download(
        repo_id="Qwen/Qwen3-VL-Embedding-2B",
        filename="scripts/qwen3_vl_embedding.py",
    )
    sys.path.insert(0, str(Path(script_path).parent))
    from qwen3_vl_embedding import Qwen3VLEmbedder  # noqa: E402

    return Qwen3VLEmbedder


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Stage 2 Image-Text Retrieval PoC")
    parser.add_argument(
        "--data-dir",
        default="./data/embedding/image_text_pairs",
        help="image-text pairs 数据目录",
    )
    parser.add_argument("--split", default="test", help="评估 split")
    parser.add_argument("--output", default="./outputs/stage2_image_text_poc.json", help="输出 JSON")
    parser.add_argument("--batch-size", type=int, default=4, help="embedding batch size")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"错误：数据目录不存在 {data_dir}")
        print("请先运行: python apps/data_cli.py build-image-pairs --parsed-dir ./data/embedding/parsed --output-dir ./data/embedding/image_text_pairs")
        sys.exit(1)

    split_file = data_dir / args.split / "data.jsonl"
    if not split_file.exists():
        print(f"错误：split 文件不存在 {split_file}")
        sys.exit(1)

    samples = []
    with split_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))

    if not samples:
        print(f"错误：{split_file} 无样本")
        sys.exit(1)

    # 过滤有 image_path 的样本
    valid = [s for s in samples if s.get("image_path")]
    if not valid:
        print("错误：无有效 image_path 样本")
        sys.exit(1)
    samples = valid

    print(f"加载 Qwen3-VL-Embedding-2B...")
    Qwen3VLEmbedder = _load_embedder()
    model = Qwen3VLEmbedder(model_name_or_path="Qwen/Qwen3-VL-Embedding-2B")
    print("模型已加载")

    data_root = data_dir.resolve()
    batch_size = args.batch_size
    image_embeddings = []
    text_embeddings = []

    for i in range(0, len(samples), batch_size):
        batch = samples[i : i + batch_size]
        img_inputs = []
        txt_inputs = []
        for s in batch:
            img_path = data_root / s["image_path"]
            if img_path.exists():
                img_inputs.append({"image": str(img_path)})
            else:
                img_inputs.append({"text": "NULL"})
            txt_inputs.append({"text": s["text"]})

        img_embs = model.process(img_inputs, normalize=True)
        txt_embs = model.process(txt_inputs, normalize=True)

        image_embeddings.append(img_embs.cpu())
        text_embeddings.append(txt_embs.cpu())

    import torch
    img_emb = torch.cat(image_embeddings, dim=0)
    txt_emb = torch.cat(text_embeddings, dim=0)
    similarity = torch.mm(img_emb, txt_emb.T)

    from packages.evaluation import compute_retrieval_metrics
    metrics = compute_retrieval_metrics(similarity)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "task_type": "ImageTextRetrieval",
        "model": "Qwen/Qwen3-VL-Embedding-2B",
        "split": args.split,
        "num_samples": len(samples),
        "metrics": metrics,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n已写入: {out_path}")


if __name__ == "__main__":
    main()
