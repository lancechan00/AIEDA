# AIEDA

AI 辅助 PCB 设计探索：基于 KiCad 开源板级数据，训练多模态模型理解走线/布局，并串联成可对话的 PCB 画线 Agent。原理图级 Agent 期待社区或合作方共建。

## 目标

**当前阶段**：`先验证模态与训练可行性，闭环 / patch / schema 后置。`

**中长期**：多模态路线 → 稳定多模态模型 → LLM + 模态 + EDA 环境 → PCB 画线 Agent。详见 [roadmap_v1.md](docs/overview/roadmap_v1.md)。

学术界已有 PCB placement/routing 标准化 benchmark [PCB-Bench](https://github.com/digailab/PCB-Bench)（ICLR 2026），可作评估参考。

若目标聚焦“输出 PCB 线路图本身”，后续输入表达应优先保留走线/网络等版图信息，而非仅压缩为统计特征。

## 任务与链路

| 任务 | 说明 |
|------|------|
| **LocalRouteChoice-Lite** | 主任务：从 5 条候选走线中选最优，geometry-only 基线 126 板 test acc 68.8% |
| **GraphTextRetrieval** | graph-text 对齐（Qwen3-Embedding-0.6B + GraphEncoder） |
| **PatchGenerationLite** | 生成式 patch 建议（Qwen-Instruct Adapter） |

DeepSeek-VL、Janus 为实验后端占位。数据按 `board-level` 切分，标签来自确定性弱标注。

## 环境

- Python 3.8+
- Windows 可直接运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pip install pytest
```

可选：复制 `.env.example` 为 `.env`，配置 `GITHUB_TOKEN` 以提升 GitHub API 额度。

## 快速开始

```powershell
# 1. 构建 fixture 数据集（仓库已带一份）
.\.venv\Scripts\python.exe .\apps\data_cli.py build --parsed-dir .\data\fixtures\parsed_boards --output-dir .\data\fixtures\local_route_choice_lite

# 2. 训练 tiny_baseline
.\.venv\Scripts\python.exe .\apps\train_cli.py --config .\configs\training\task_v1.yaml

# 3. 评估
.\.venv\Scripts\python.exe .\apps\eval_cli.py --config .\configs\training\task_v1.yaml --checkpoint .\outputs\tiny_baseline_fixture\checkpoints\best_model.pt --split test
```

### 其他链路

**GraphTextRetrieval**：见 [qwen_embedding_runbook_v1.md](docs/training/qwen_embedding_runbook_v1.md)

**PatchGeneration**：见 [patch_generation_adapter_v1.md](docs/training/patch_generation_adapter_v1.md)

**GitHub 采集**：`.\scripts\run_kicad_github_pipeline.ps1`

## 文档

| 类别 | 文档 |
|------|------|
| 目标与路线 | [project_goal.md](docs/overview/project_goal.md) · [roadmap_v1.md](docs/overview/roadmap_v1.md) · [decision_log_v1.md](docs/overview/decision_log_v1.md) |
| 训练 | [task_v1.md](docs/training/task_v1.md) · [baseline_local_route_choice_126.md](docs/training/baseline_local_route_choice_126.md) · [experiment_results_260312.md](docs/training/experiment_results_260312.md) |
| 数据 | [kicad_dataset_plan.md](docs/data/kicad_dataset_plan.md) · [annotation_strategy_v1.md](docs/data/annotation_strategy_v1.md) |
| 系统 | [privacy_path_audit.md](docs/system/privacy_path_audit.md) · [open_source_pipeline.md](docs/system/open_source_pipeline.md) |

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\unit
```
