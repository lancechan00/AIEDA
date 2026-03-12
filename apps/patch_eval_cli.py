#!/usr/bin/env python3
"""Patch 生成评估 CLI。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.training import GenerativeTrainer, GenerativeTrainingConfig


@click.command()
@click.option("--config", type=click.Path(exists=True), required=True, help="生成训练配置文件")
@click.option("--checkpoint", type=click.Path(exists=True), required=True, help="模型检查点")
@click.option("--split", default="test", type=click.Choice(["train", "val", "test"]), show_default=True)
@click.option("--closed-loop", is_flag=True, help="运行闭环验证：通过 PatchFeedbackBridge (Mock) 校验可执行性")
def main(config: str, checkpoint: str, split: str, closed_loop: bool) -> None:
    eval_config = GenerativeTrainingConfig.from_yaml(config)
    trainer = GenerativeTrainer(eval_config)
    metrics = trainer.evaluate(split=split, checkpoint_path=checkpoint, run_closed_loop=closed_loop)
    click.echo(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
