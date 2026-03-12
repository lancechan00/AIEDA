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

### 5.3 126 板扩数据 Qwen-Instruct Adapter（2026-03-12）

基于与 LocalRouteChoice 相同的扩数据源（`data/embedding/parsed`，126 板），重建 PatchGenerationLite 并跑通 Qwen-Instruct adapter 链路。

| 项目 | 值 |
|------|-----|
| 数据目录 | `data/patch_generation_lite` |
| 数据来源 | `data/embedding/parsed`（与 126 板 LocalRouteChoice 同源） |
| train 样本/板 | 483 / 124 |
| val 样本/板 | 64 / 1 |
| test 样本/板 | 64 / 1 |
| 配置 | `configs/training/patch_generation_qwen_instruct.yaml` |
| epochs | 6 |
| load_pretrained | true |
| checkpoint | `outputs/patch_generation_qwen_instruct/checkpoints/best_model.pt` |

**Test 评估（open-loop）**：

| 指标 | 值 |
|------|-----|
| loss | 3.84e-06 |
| parse_success_rate | **1.0** |
| field_completeness_rate | **1.0** |
| op_match_rate | **1.0** |
| net_id_match_rate | **1.0** |
| params_exact_rate | **1.0** |
| action_exact_match | **1.0** |

**Test 评估（closed-loop Mock）**：

| 指标 | 值 |
|------|-----|
| execution_accept_rate | **1.0** |

**结论**：adapter 和结构化输出链已稳定；open-loop 全指标 100%（parse、字段、op、net_id、params、action_exact_match），closed-loop Mock execution_accept 100%。可解析、字段完整且通过 Mock 结构校验，动作级精确匹配达标。

## 6. 下一步建议

1. Patch 生成：接入本地 Qwen-Instruct 预训练权重，重跑训练与抽样；闭环验证使用 `--closed-loop` 跑 Mock PatchFeedbackBridge
2. LocalRouteChoice：收敛为 geometry-only 基线（`task_v1.yaml` / `task_v1_github.yaml` 已默认仅 geometry）
3. 视结果决定是否接入 DeepSeek-VL / Janus 同任务推理

## 7. GPU 投入决策（2026-03-12）

**暂缓更高配置 GPU**：在以下条件满足前，A4000 16G 足够支撑当前实验。

考虑 GPU 升级的时机：

1. 准备训练/微调真正的多模态后端（DeepSeek-VL、Janus），而非 tiny baseline 或 0.5B 级文本模型
2. 训练已被 batch_size、max_length、分辨率或多模态输入 packing 明显卡住
3. 关键路线验证已证明有效，下一步主要矛盾变为“训练太慢、实验周转太慢”

## 8. 126 板正式基线 (2026-03-12)

扩数据后 (126 board-level) 的 geometry-only 结果已固化为正式基线：

| 指标 | 扩数据前 (18 板) | 扩数据后 (126 板) |
|------|------------------|-------------------|
| test accuracy | 25% | **68.8%** |
| test top_3 | 75–80% | **89.1%** |
| val best_acc | 20.3% | **59.4%** |

详见 [baseline_local_route_choice_126.md](baseline_local_route_choice_126.md)。后续所有改动均与此基线对比。

参考：`docs/training/local_route_choice_runbook_v1.md`、`docs/training/qwen_embedding_runbook_v1.md`

## 9. 验证实验清单（2026-03-12 执行）

### 9.1 geometry-only 多 seed 复现

| seed | test acc | test top_3 | test loss |
|------|----------|------------|-----------|
| 7 | **68.75%** | 89.1% | 1.05 |
| 42 | 50.0% | 89.1% | 1.25 |
| 123 | 51.6% | 87.5% | 1.11 |

**结论**：test acc 波动大（50%–68.75%），说明基线对 seed 敏感。seed 7 复现了此前 68.8% 基线，但 42/123 明显偏低，建议后续增加 epochs 或调整超参以稳定。

### 9.2 GraphTextRetrieval 训练与评估

| 指标 | val (3 epochs) | test |
|------|----------------|------|
| recall_at_1 | 0.5 | **0.333** |
| recall_at_3 | 1.0 | **1.0** |
| recall_at_5 | 1.0 | **1.0** |
| mrr | 0.75 | **0.61** |

### 9.3 retrieval 噪声敏感性

| noise_std | recall_at_1 | recall_at_3 | mrr |
|-----------|-------------|-------------|-----|
| 0.0 | 0.333 | 1.0 | 0.61 |
| 0.05 | 0.333 | 1.0 | 0.61 |

**结论**：noise_std=0.05 下指标无下降，对轻微噪声鲁棒。

### 9.4 实验执行命令速查

| 实验 | 命令 |
|------|------|
| 多 seed LocalRouteChoice | `.\scripts\run_multi_seed_local_route_choice.ps1` |
| GraphTextRetrieval 训练 | `python .\apps\embedding_train_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml` |
| retrieval 评估 | `python .\apps\embedding_eval_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml --checkpoint .\outputs\qwen3_embedding_graph_text\checkpoints\best_model.pt --split test` |
| 噪声验证 | `--noise-std 0.05` 同上 |
| 合并多 seed 报告 | `python .\scripts\merge_multi_seed_report.py --audit .\outputs\multi_seed_audit.json --evals .\outputs\eval_seed*.json` |

### 9.5 Qwen3-VL-Embedding-2B PoC

待实现：需接入 `Qwen/Qwen3-VL-Embedding-2B`，对 PCB 渲染图做 image embedding，与当前 graph-text 检索对比。详见 `docs/training/memo_multimodal_embedding_v1.md`。

