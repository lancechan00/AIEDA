#!/usr/bin/env python3
"""最小评估 CLI。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.training import Trainer, TrainingConfig


@click.command()
@click.option("--config", type=click.Path(exists=True), required=True, help="训练配置文件")
@click.option("--checkpoint", type=click.Path(exists=True), required=True, help="模型检查点")
@click.option("--split", default="test", type=click.Choice(["train", "val", "test"]), show_default=True)
def main(config: str, checkpoint: str, split: str) -> None:
    train_config = TrainingConfig.from_yaml(config)
    trainer = Trainer(train_config)
    metrics = trainer.evaluate(split=split, checkpoint_path=checkpoint)
    click.echo(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()