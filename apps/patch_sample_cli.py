#!/usr/bin/env python3
"""Patch 生成抽样对比：输出 prompt / target / pred 三联。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.models import PcbMultimodalAdapter, get_backend
from packages.training import GenerativeTrainingConfig
from packages.training.datasets import PatchGenerationDatasetBuilder


@click.command()
@click.option("--config", type=click.Path(exists=True), required=True, help="生成训练配置文件")
@click.option("--checkpoint", type=click.Path(exists=True), required=True, help="模型检查点")
@click.option("--split", default="test", type=click.Choice(["train", "val", "test"]), show_default=True)
@click.option("--num-samples", default=5, type=int, show_default=True, help="抽样数量")
def main(config: str, checkpoint: str, split: str, num_samples: int) -> None:
    cfg = GenerativeTrainingConfig.from_yaml(config)
    backend_cls = get_backend(cfg.model_name)
    model = backend_cls(
        task_type=cfg.task_type,
        text_model_name=cfg.text_model_name,
        load_pretrained=cfg.load_pretrained,
        local_files_only=cfg.local_files_only,
    )
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(checkpoint, map_location=device, weights_only=True)
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)
    model.eval()

    tokenizer = model.tokenizer
    adapter = PcbMultimodalAdapter()
    dataset = PatchGenerationDatasetBuilder.create_dataset(cfg.dataset_path, split=split)

    for idx in range(min(num_samples, len(dataset))):
        sample = dataset[idx]
        prompt = adapter.format_prompt(sample["instruction"], sample["context_text"])
        target = sample["target_patch"]

        enc = tokenizer(
            [prompt],
            truncation=True,
            max_length=cfg.max_input_length,
            padding=True,
            return_tensors="pt",
            add_special_tokens=False,
        )
        input_ids = enc["input_ids"].to(device)
        attn = enc["attention_mask"].to(device)

        with torch.no_grad():
            generated = model.generate(
                input_ids=input_ids,
                attention_mask=attn,
                max_new_tokens=cfg.generation_max_new_tokens,
            )

        if hasattr(tokenizer, "batch_decode"):
            full_text = tokenizer.batch_decode(generated.tolist(), skip_special_tokens=True)[0]
        else:
            full_text = tokenizer.decode(generated[0].tolist(), skip_special_tokens=True)
        pred = full_text[len(prompt) :].strip() if full_text.startswith(prompt) else full_text.strip()

        click.echo(f"\n--- Sample {idx + 1} ---")
        click.echo(f"[PROMPT] (truncated) ...{prompt[-200:]}")
        click.echo(f"[TARGET] {target[:300]}{'...' if len(target) > 300 else ''}")
        click.echo(f"[PRED]   {pred[:300]}{'...' if len(pred) > 300 else ''}")


if __name__ == "__main__":
    main()
