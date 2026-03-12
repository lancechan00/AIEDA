#!/usr/bin/env python3
"""Qwen embedding 训练 CLI。"""

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
@click.option("--output-dir", type=click.Path(), default=None, help="覆盖输出目录")
def main(config: str, output_dir: str | None) -> None:
    train_config = EmbeddingTrainingConfig.from_yaml(config)
    trainer = EmbeddingTrainer(train_config, output_dir=output_dir)
    summary = trainer.train()
    click.echo(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
