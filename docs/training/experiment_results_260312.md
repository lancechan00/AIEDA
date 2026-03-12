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
- **数据切分修复**：sample-aware split，保证 val/test 分配到有样本的板（val 从 0 → 64 样本）
- **LocalRouteChoice-Lite GitHub**：train 320 样本、val 64、test 64

## 4. GitHub 数据消融结果（8 epochs，val 非空）

| 配置 | val best_acc | test acc | test top_3 | test loss |
|------|--------------|----------|------------|-----------|
| geometry + image | 20.3% | 25.0% | 81.3% | 1.75 |
| geometry only | 20.3% | 25.0% | **82.8%** | **1.60** |
| image only | 20.3% | 25.0% | 81.3% | 1.61 |

**结论**：
- 三组 test acc 均为 25%（高于随机 20%），说明任务有学习信号
- geometry-only 的 test top_3 略优（82.8%）、test loss 最低（1.60）
- image 模态在当前小规模数据上未带来明显增益，可考虑后续扩数据再验证

## 5. PatchGenerationLite 结果

### 5.1 Fallback 模型（首轮）

- **后端**：离线 fallback（未加载预训练）
- **结果**：train loss 3.92，val 2.11，test 2.14；parse_success 0
- **修复**：batch 构造先截断 prompt 再拼接 target，避免 NaN

### 5.2 预训练 Qwen2.5-0.5B-Instruct

- **配置**：load_pretrained=true，batch_size=1，max_input=512，max_target=128，2 epochs
- **训练**：train loss 0.04→0.02，val loss 0.35→0.45
- **Val**：parse_success_rate **1.0**，field_completeness_rate **1.0**
- **Test**：parse_success_rate **87.5%**，field_completeness_rate **87.5%**，action_exact_match 0

**结论**：预训练 Qwen 能稳定产出可解析的 Patch JSON 结构，字段完整率达标；动作级精确匹配尚需更多训练或数据。

## 6. 下一步建议

1. Patch 生成：接入本地 Qwen-Instruct 预训练权重，重跑训练与抽样
2. 视数据规模决定是否保留 image 模态（LocalRouteChoice）
3. 视结果决定是否接入 DeepSeek-VL / Janus 同任务推理
