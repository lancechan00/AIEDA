#!/usr/bin/env python3
"""Qwen embedding 检索评估 CLI。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.training import EmbeddingTrainer, EmbeddingTrainingConfig


@click.command()
@click.option("--config", type=click.Path(exists=True), required=True, help="embedding 训练配置文件")
@click.option("--checkpoint", type=click.Path(exists=True), required=True, help="graph encoder checkpoint 路径")
@click.option("--split", type=str, default="test", show_default=True, help="评估 split")
@click.option("--noise-std", type=float, default=0.0, show_default=True, help="图特征高斯噪声强度")
def main(config: str, checkpoint: str, split: str, noise_std: float) -> None:
    eval_config = EmbeddingTrainingConfig.from_yaml(config)
    trainer = EmbeddingTrainer(eval_config)
    metrics = trainer.evaluate(split=split, checkpoint_path=checkpoint, noise_std=noise_std)
    click.echo(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
