# PatchGeneration Adapter V1

## 1. 目标

在不直接接入视觉大模型的前提下，先跑通一条可训练生成链：

- 输入：PCB 多模态状态（当前先序列化为文本）
- 后端：本地 `Qwen-Instruct` 风格生成模型接口
- 输出：可执行 `Patch DSL` 文本
- 评估：语法可解析、字段完整、动作级匹配

该链路用于验证：

1. PCB 专用 adapter 是否能稳定组织上下文；
2. 生成模型是否能稳定输出结构化 patch；
3. 后续接入 EDA 闭环和视觉后端时，接口是否可复用。

## 2. 当前实现边界

### 2.1 已实现

- 数据构建：`apps/data_cli.py build-patches`
- 任务类型：`PatchGenerationLite`
- 序列化：`PatchPromptSerializer` 输出 `context_text`
- 训练器：`GenerativeTrainer`
- 后端：`qwen_instruct`（支持离线 fallback）
- 评估：`parse_success_rate`、`field_completeness_rate`、`action_exact_match`
- 闭环接口：`PatchFeedbackBridge` 占位

### 2.2 暂不实现

- 真实 `env.step(patch)` 执行
- DRC 驱动奖励优化（PPO / rejection sampling）
- 原生视觉多模态输入（Qwen-VL / Janus / DeepSeek-VL）

## 3. 数据与样本格式

每条样本包含：

- `instruction`: 任务指令
- `context_text`: 序列化的 board/local/rules 信息
- `target_patch`: 目标 patch（JSON 字符串）
- `metadata`: `board_id`、`net_id`、`source_type`、`op` 等

当前 `short-patch` 子集先覆盖：

- `add_trace`
- `add_via`

## 4. 训练与评估命令

### 4.1 构建数据

```powershell
python .\apps\data_cli.py build-patches --parsed-dir .\data\embedding\parsed --output-dir .\data\patch_generation_lite
```

### 4.2 训练

```powershell
python .\apps\patch_train_cli.py --config .\configs\training\patch_generation_qwen_instruct.yaml
```

### 4.3 评估

```powershell
python .\apps\patch_eval_cli.py --config .\configs\training\patch_generation_qwen_instruct.yaml --checkpoint .\outputs\patch_generation_qwen_instruct\checkpoints\best_model.pt --split test
```

## 5. 升级路径

### Stage A: 文本序列化生成（当前）

`geometry/graph/rules -> context_text -> qwen_instruct -> Patch DSL`

目标：验证生成链和结构化输出稳定性。

### Stage B: 原生多模态输入

替换 adapter 输入侧：

- 从 `context_text` 为主
- 升级为 `image + structured_text (+geometry projector)`

但保持以下接口不变：

- 数据集字段中的 `instruction/target_patch`
- 训练器输出格式与 checkpoint 机制
- Patch 评估器和解析器

### Stage C: 状态反馈闭环

将 `PatchFeedbackBridge` 从占位改成真实执行：

1. `apply_patch(patch)` 执行 patch；
2. 返回 DRC 与 board snapshot；
3. 将反馈注入下一轮 prompt；
4. 模型输出 diff/patch 修正。

## 6. 推荐实践

1. 先用小样本、低 epoch 跑通格式正确率；
2. 再提高上下文复杂度（更多 graph/rules）；
3. 最后再上视觉塔和闭环，不要三件事同时推进；
4. 训练集始终保持 board-level split，避免泄漏。
