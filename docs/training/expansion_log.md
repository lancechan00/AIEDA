# LocalRouteChoice-Lite 扩数收益跟踪

每轮扩数后记录板数、样本数与指标变化，用于判断扩数边际收益。

## 跟踪表

| 轮次 | 日期 | train 板数 | val 板数 | test 板数 | train 样本 | val 样本 | test 样本 | test acc (seed7) | test top_3 | val best_acc | 备注 |
|------|------|------------|----------|-----------|------------|----------|-----------|-----------------|------------|--------------|------|
| 0 (18板) | 2026-03-12 | — | — | — | 320 | 64 | 64 | 25% | 75–80% | 20.3% | 扩数前基线 |
| 1 (126板) | 2026-03-12 | 124 | 1 | 1 | 483 | 64 | 64 | 68.8% | 89.1% | 59.4% | 正式基线 |
| 2 | | | | | | | | | | | |

## 使用说明

1. 扩数前：在 `data/embedding/github_whitelist.json` 中添加新仓库（参考 [data_expansion_guide_v1.md](data_expansion_guide_v1.md) 5.2）。
2. 运行：`.\scripts\run_board_expansion.ps1`
3. 训练评估：`.\scripts\run_multi_seed_local_route_choice.ps1` 或单 seed：`python apps/train_cli.py --config configs/training/task_v1_github.yaml`。
4. 将 `dataset_summary.json` 与 eval 结果填入上表新行。

## 决策门槛

- 新增板子后 test accuracy 仍能提升 → 继续扩数。
- 指标趋于平台、波动收窄 → 考虑进入下一阶段（patch 生成闭环、多模态后端）。
- 参考 [stage_gate_checklist.md](stage_gate_checklist.md)。
