# 实验记录 2026-03-12

## 1. 配置变更

- `task_v1.yaml`: `epochs` 1 → 8
- 新增消融配置：
  - `task_v1_geometry_only.yaml`: 仅 geometry 模态
  - `task_v1_image_only.yaml`: 仅 image 模态

## 2. LocalRouteChoice-Lite 消融结果（fixture 数据，8 epochs）

| 配置 | val best_acc | test acc | test top_3 | test loss |
|------|--------------|----------|-----------|-----------|
| geometry + image | 0.5 | 0.0 | 1.0 | 1.59 |
| geometry only | 0.0 | **0.5** | **1.0** | **1.46** |
| image only | 0.5 | 0.0 | 0.5 | 1.60 |

**说明**：fixture 仅 3 块板、样本极少，结论仅供参考。geometry-only 在测试集上表现最好，可能与当前弱标注/数据分布有关。

## 3. 扩数据与 KiCad 解析修复

- **KiCad 解析器**：修正 `_parse_tracks` 正则，兼容 KiCad 6/7 格式（`layer` 无引号、可选 `tstamp`）
- **LocalRouteChoice-Lite GitHub**：train 384 样本、val 0、test 64
- **训练结果**（`task_v1_github.yaml`，8 epochs）：
  - train acc: 33.6% → 38.9%，top_3: 73% → 79%
  - test acc: **25%**，top_3: **84.4%**（明显高于随机 20%）

## 4. 下一步建议

1. 等 pipeline 完成，用 GitHub 数据重跑训练与消融
2. 在更大数据上验证 geometry vs image 的贡献
3. 视结果决定是否接入 DeepSeek-VL / Janus 同任务推理
