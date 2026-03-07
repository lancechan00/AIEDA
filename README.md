# AIEDA

第一阶段的正式目标只有一句话：

`先验证模态与训练可行性，闭环 / patch / schema 后置。`

当前仓库只保留一个主任务：

`LocalRouteChoice-Lite`

## 当前范围

- 从 KiCad 板级数据提取局部走线样本。
- 使用确定性弱标注生成方向标签。
- 按 `board-level` 划分 `train`、`val`、`test`。
- 用 `tiny_baseline` 跑通最小训练与评估闭环。
- 将 `DeepSeek-VL`、`Janus` 保留为实验后端接口占位。

## 环境

- Python 3.8+
- Windows 可直接运行

安装：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pytest
```

## 快速开始

### 1. 构建内置 fixture 数据集

```powershell
.\.venv\Scripts\python.exe .\apps\data_cli.py build --parsed-dir .\data\fixtures\parsed_boards --output-dir .\data\fixtures\local_route_choice_lite
```

仓库默认已经带有一份构建好的小数据集，配置文件直接指向它：

- `data/fixtures/local_route_choice_lite`
- `configs/training/task_v1.yaml`

### 2. 训练 `tiny_baseline`

```powershell
.\.venv\Scripts\python.exe .\apps\train_cli.py --config .\configs\training\task_v1.yaml
```

### 3. 在测试集上评估

```powershell
.\.venv\Scripts\python.exe .\apps\eval_cli.py --config .\configs\training\task_v1.yaml --checkpoint .\outputs\tiny_baseline_fixture\checkpoints\best_model.pt --split test
```

## CLI

数据相关：

```powershell
.\.venv\Scripts\python.exe .\apps\data_cli.py build --parsed-dir .\data\fixtures\parsed_boards --output-dir .\data\fixtures\local_route_choice_lite
.\.venv\Scripts\python.exe .\apps\data_cli.py validate --data-dir .\data\fixtures\local_route_choice_lite
```

训练与评估：

```powershell
.\.venv\Scripts\python.exe .\apps\train_cli.py --config .\configs\training\task_v1.yaml
.\.venv\Scripts\python.exe .\apps\eval_cli.py --config .\configs\training\task_v1.yaml --checkpoint .\outputs\tiny_baseline_fixture\checkpoints\best_model.pt --split test
```

## 文档入口

- `docs/overview/project_goal.md`
- `docs/overview/decision_log_v1.md`
- `docs/training/task_v1.md`
- `docs/modules/model_backends.md`
- `docs/data/kicad_dataset_plan.md`
- `docs/data/annotation_strategy_v1.md`

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\unit
```
