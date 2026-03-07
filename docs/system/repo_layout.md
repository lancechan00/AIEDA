# 当前仓库结构

第一阶段只保留真正参与最小闭环的结构。

## 核心目录

- `apps/`
  Python CLI 入口，当前只保留 `train`、`data`、`eval`。

- `packages/data_pipeline/`
  KiCad 解析、样本提取、数据集构建。

- `packages/models/backends/`
  `tiny_baseline` 与实验后端占位。

- `packages/training/`
  配置、数据集读取、训练器。

- `packages/evaluation/`
  最小评估指标。

- `data/fixtures/`
  仓库自带的小型 parsed boards 和可运行 fixture 数据集。

- `tests/unit/`
  parser、dataset build、train、eval smoke tests。

## 当前默认工作流

1. 从 `data/fixtures/parsed_boards/` 构建数据集，或直接使用内置 fixture。
2. 用 `configs/training/task_v1.yaml` 运行 `tiny_baseline`。
3. 在 `test` split 上执行评估。

## 后置目录约束

以下方向可以保留讨论，但不应主导第一阶段实现顺序：

- 环境闭环。
- patch 生成。
- schema 驱动执行。
- 多任务平台化抽象。
