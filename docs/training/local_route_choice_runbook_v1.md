# LocalRouteChoice-Lite 训练 Runbook (v1)

## 1. 基线配置

**v1 默认基线**：`geometry-only`（仅几何张量，暂不包含 image 模态）。

依据 260312 消融结果：geometry-only 在 test top_3 与 test loss 上略优于 geometry+image，在小规模数据下 image 未带来明显增益。

## 2. 配置文件

| 配置 | 数据 | 用途 |
|------|------|------|
| `configs/training/task_v1.yaml` | fixture | 本地调试、smoke |
| `configs/training/task_v1_github.yaml` | GitHub | 正式实验 |

两配置均使用 `modalities: [geometry]`。

## 3. 固定评估口径

评估指标（与 `packages/evaluation/metrics.py` 一致）：

- `accuracy`：单标签准确率（5 分类：up/down/left/right/stop）
- `top_3_accuracy`：Top-3 命中率

切分规则：

- 按 **board-level** 划分 train/val/test
- 同一块板子的样本不跨 split

## 4. 训练与评估命令

### Fixture 数据（小样本）

```powershell
python .\apps\train_cli.py --config .\configs\training\task_v1.yaml
python .\apps\eval_cli.py --config .\configs\training\task_v1.yaml --checkpoint .\outputs\tiny_baseline_fixture\checkpoints\best_model.pt --split test
```

### GitHub 数据

```powershell
python .\apps\train_cli.py --config .\configs\training\task_v1_github.yaml
python .\apps\eval_cli.py --config .\configs\training\task_v1_github.yaml --checkpoint .\outputs\tiny_baseline_github\checkpoints\best_model.pt --split test
```

## 5. 数据准备

```powershell
python .\apps\data_cli.py build --parsed-dir .\data\embedding\parsed --output-dir .\data\local_route_choice_lite_github
```

参考 `scripts/run_kicad_github_pipeline.ps1` 完成 GitHub 采集与解析。

## 6. 多 seed 复现与审计

```powershell
.\scripts\run_multi_seed_local_route_choice.ps1
```

运行 3 个 seed (7, 42, 123)，训练、评估并合并报告到 `outputs/multi_seed_audit.json`。用于判断基线是否稳定。

类别分布审计：

```powershell
python scripts/audit_local_route_choice_dataset.py --data-dir ./data/local_route_choice_lite_github --output outputs/audit_label_distribution.json
```

## 7. 扩数与收益跟踪

扩数一键流程（在已更新白名单后）：

```powershell
.\scripts\run_board_expansion.ps1
```

每轮扩数后，将 board 数、样本数、test accuracy 记录到 [expansion_log.md](expansion_log.md)。基线与 stage-gate 参考 [baseline_local_route_choice_126.md](baseline_local_route_choice_126.md)、[stage_gate_checklist.md](stage_gate_checklist.md)。

## 8. 后续扩数建议

扩数时优先增加 **板级多样性**，而非同一板上堆样本：

- 增加 board 数量
- 保持 board-level split
- 审计类别分布（up/down/left/right/stop）是否偏斜
