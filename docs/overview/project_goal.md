# AIEDA 第一阶段目标

第一阶段的正式目标只有一句话：

`先验证模态与训练可行性，闭环 / patch / schema 后置。`

## 唯一主问题

用开源 KiCad 板子构造一个 `LocalRouteChoice-Lite` 任务，在同一任务上比较：

- `tiny_baseline`
- `DeepSeek-VL`
- `Janus`

第一阶段要回答的是：

1. 哪些输入模态值得保留。
2. `tiny_baseline` 是否能跑通最小训练链。
3. `DeepSeek-VL` 和 `Janus` 是否值得继续作为同任务实验后端。

## 本阶段保留内容

- 真实 KiCad 数据解析。
- 基于真实走线的确定性弱标注。
- `board-level` 数据切分。
- `train -> val -> eval` 最小闭环。
- Windows 可直接执行的 Python CLI。

## 本阶段明确后置

- 闭环环境。
- `patch` 生成。
- `schema` 主导的执行框架。
- 多任务联合训练。
- LoRA 或大模型微调主链。

## 成功标准

第一阶段完成时，仓库至少应满足：

1. 正式文档口径一致，不再以环境闭环驱动实现顺序。
2. 只保留 `LocalRouteChoice-Lite` 一个主任务。
3. 仓库自带小数据可真实跑完一次 `train -> val -> eval`。
4. 训练标签来自确定性弱标注，而不是随机 mock。
5. 数据切分按 `board-level` 执行。
