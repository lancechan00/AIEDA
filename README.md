# AIEDA

AIEDA 是一个探索项目。Idea 起源于一次画板后，认为 AI 模型画 PCB 图有潜力，可极大加速电子开发验证时间，于是对模型技术进行探索。

## 项目关键实施

1. 介绍与 ChatGPT 讨论的聊天记录；
2. 继续深入研究；
3. 得出大致框架；
4. 利用 Cursor 搭建框架，完成一次简单训练。

- `pre_design/Snipaste_2026-03-07_12-17-10.png` 是一张架构图，能最直观地了解项目目标；
- `pre_design` 的其余文件，高度概括了从 ChatGPT/Grok 总结下来的目标；
- `docs` 是从 `pre_design` 分解的文档；
- 其它文件是 Cursor Agent 基于 `pre_design` 和 `docs` 创建出来的 monorepo 目录。

小结：通过探索的方式，展示了我对目前 AI 工具的熟练度和一部分习惯，以及我对 AI 项目探索的热情。



## 开始

第一阶段的正式目标只有一句话：

`先验证模态与训练可行性，闭环 / patch / schema 后置。`

当前仓库只保留一个主任务：

`LocalRouteChoice-Lite`

同时新增一个并行实验链路：

`GraphTextRetrieval (Qwen3-Embedding-0.6B)`

以及一个生成式实验链路：

`PatchGenerationLite (Qwen-Instruct Adapter)`

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

可选：复制 `.env.example` 为 `.env`，配置 `GITHUB_TOKEN` 以提升 GitHub discovery 的 API 额度。

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

Qwen3 embedding 相关：

```powershell
.\.venv\Scripts\python.exe .\apps\data_cli.py audit-sources --source-dir .\data\embedding\raw --output-file .\data\embedding\raw_manifest.json
.\.venv\Scripts\python.exe .\apps\data_cli.py parse --source-dir .\data\embedding\raw --output-dir .\data\embedding\parsed --parallel 4
.\.venv\Scripts\python.exe .\apps\data_cli.py build-pairs --parsed-dir .\data\embedding\parsed --output-dir .\data\embedding\graph_text_pairs --seed 7 --negatives-per-sample 2
.\.venv\Scripts\python.exe .\apps\embedding_train_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml
.\.venv\Scripts\python.exe .\apps\embedding_eval_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml --checkpoint .\outputs\qwen3_embedding_graph_text\checkpoints\best_model.pt --split test
```

Patch 生成相关：

```powershell
.\.venv\Scripts\python.exe .\apps\data_cli.py build-patches --parsed-dir .\data\embedding\parsed --output-dir .\data\patch_generation_lite
.\.venv\Scripts\python.exe .\apps\patch_train_cli.py --config .\configs\training\patch_generation_qwen_instruct.yaml
.\.venv\Scripts\python.exe .\apps\patch_eval_cli.py --config .\configs\training\patch_generation_qwen_instruct.yaml --checkpoint .\outputs\patch_generation_qwen_instruct\checkpoints\best_model.pt --split test
```

GitHub 采集 + A4000 调试快捷脚本：

```powershell
.\scripts\run_kicad_github_pipeline.ps1
.\scripts\run_embedding_a4000_debug.ps1
.\scripts\run_embedding_docker.ps1
```

## 文档入口

- `docs/overview/project_goal.md`
- `docs/system/privacy_path_audit.md`（开源前隐私与路径审计）
- `docs/system/open_source_pipeline.md`（脱敏路径下的完整爬虫+训练流程）
- `docs/system/github_reset_guide.md`（GitHub 重置提交、清除历史敏感信息）
- `docs/overview/decision_log_v1.md`
- `docs/training/task_v1.md`
- `docs/training/qwen_embedding_runbook_v1.md`
- `docs/training/patch_generation_adapter_v1.md`
- `docs/modules/model_backends.md`
- `docs/data/kicad_dataset_plan.md`
- `docs/data/annotation_strategy_v1.md`
- `docs/data/kicad_source_policy_v1.md`
- `docs/data/graph_text_pair_schema_v1.md`

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\unit
```
