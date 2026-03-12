# LocalRouteChoice-Lite 正式基线（126 板）

本文档记录扩数据后的正式基线，作为后续改动对照。

## 1. 数据版本

| 项目 | 值 |
|------|-----|
| 数据目录 | `data/local_route_choice_lite_github` |
| 板数 | 126（train 124, val 1, test 1） |
| train 样本数 | 483 |
| val 样本数 | 64 |
| test 样本数 | 64 |
| 来源 | `data/embedding/parsed`（GitHub + KiCad demo） |
| 构建命令 | `python apps/data_cli.py build --parsed-dir data/embedding/parsed --output-dir data/local_route_choice_lite_github` |
| 切分规则 | board-level，sample-aware |

参考 `data/local_route_choice_lite_github/dataset_summary.json` 获取完整 board 列表。

## 2. 配置

| 项目 | 值 |
|------|-----|
| 配置文件 | `configs/training/task_v1_github.yaml` |
| 模态 | geometry-only |
| seed | 7 |
| epochs | 8 |
| batch_size | 8 |
| learning_rate | 0.001 |
| 输出目录 | `outputs/tiny_baseline_github` |

## 3. 指标（扩数据前后对比）

| 指标 | 扩数据前 (18 板) | 扩数据后 (126 板) |
|------|------------------|-------------------|
| test accuracy | 25% | **68.8%** |
| test top_3 | 75–80% | **89.1%** |
| val best_acc | 20.3% | **59.4%** |

## 4. 复现命令

```powershell
python .\apps\train_cli.py --config .\configs\training\task_v1_github.yaml
python .\apps\eval_cli.py --config .\configs\training\task_v1_github.yaml --checkpoint .\outputs\tiny_baseline_github\checkpoints\best_model.pt --split test
```

## 5. 标签分布审计（126 板）

```powershell
python scripts/audit_local_route_choice_dataset.py --data-dir ./data/local_route_choice_lite_github --output outputs/audit_label_distribution_126.json
```

典型结论（示例输出）：

| split | up | down | left | right | stop |
|-------|----|------|------|-------|------|
| train | 12.2% | 7.9% | 20.7% | **47.8%** | 11.4% |
| val | 6.2% | 25.0% | **37.5%** | 20.3% | 10.9% |
| test | 7.8% | 10.9% | **39.1%** | 25.0% | 17.2% |

- train 中 `right` 占比较高（约 48%），存在类别偏斜
- val/test 由单板决定，与 train 分布不同，属于正常 board-level 划分
- 建议后续扩数时关注类别平衡，必要时做重采样或类别权重

## 6. 多 seed 复现

```powershell
.\scripts\run_multi_seed_local_route_choice.ps1
```

运行 3 个 seed (7, 42, 123)，审计结果写入 `outputs/multi_seed_audit.json`，各 seed 输出目录 `outputs/tiny_baseline_github_seed*`。

**实测结果（126 板，2026-03-12 运行）**：

| seed | test accuracy | test top_3 | val best_acc |
|------|---------------|------------|--------------|
| 7 | **65.6%** | **89.1%** | 54.7% |
| 42 | 46.9% | **92.2%** | 48.4% |
| 123 | 51.6% | 87.5% | 45.3% |

**结论**：test accuracy 存在明显波动（46.9%–65.6%），受 val 单板选择与收敛随机性影响；top_3 相对稳定（87.5%–92.2%）。建议扩数后重跑多 seed 验证，并在扩数时增加 val/test 板数以降低方差。

## 7. 参考

- [experiment_results_260312.md](experiment_results_260312.md)：历史实验记录
- [local_route_choice_runbook_v1.md](local_route_choice_runbook_v1.md)：训练与评估口径
- [data_expansion_guide_v1.md](data_expansion_guide_v1.md)：扩数策略
