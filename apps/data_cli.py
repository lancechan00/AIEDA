#!/usr/bin/env python3
"""最小数据 CLI。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.data_pipeline.loaders import DatasetLoader
from packages.data_pipeline.parsers import KiCadParser


@click.group()
def main() -> None:
    """解析与构建第一阶段数据。"""


@main.command("parse")
@click.option("--source-dir", type=click.Path(exists=True), required=True, help="KiCad 项目目录")
@click.option("--output-dir", type=click.Path(), required=True, help="解析结果目录")
@click.option("--parallel", default=1, show_default=True, help="并行数")
def parse_command(source_dir: str, output_dir: str, parallel: int) -> None:
    parser = KiCadParser()
    parser.parse_projects(source_dir, output_dir, parallel)
    click.echo(f"parsed -> {output_dir}")


@main.command("build")
@click.option("--parsed-dir", type=click.Path(exists=True), required=True, help="解析后 JSON 目录")
@click.option("--output-dir", type=click.Path(), required=True, help="输出数据集目录")
def build_command(parsed_dir: str, output_dir: str) -> None:
    loader = DatasetLoader()
    summary = loader.build_dataset(parsed_dir, output_dir, task_type="LocalRouteChoiceLite")
    click.echo(json.dumps(summary, indent=2, ensure_ascii=False))


@main.command("validate")
@click.option("--data-dir", type=click.Path(exists=True), required=True, help="数据集目录")
def validate_command(data_dir: str) -> None:
    loader = DatasetLoader()
    summary = loader.validate_dataset(data_dir)
    click.echo(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()