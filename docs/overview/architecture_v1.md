# 架构说明（降级文档）

这个文档不再主导第一阶段实现顺序。

第一阶段正式目标不是环境闭环，而是：

`先验证模态与训练可行性，闭环 / patch / schema 后置。`

## 当前生效的最小架构

第一阶段只要求下面这条链路成立：

1. KiCad 解析得到板级 JSON。
2. 从真实走线提取 `LocalRouteChoice-Lite` 样本。
3. 用确定性弱标注生成方向标签。
4. 按 `board-level` 划分 `train`、`val`、`test`。
5. 用 `tiny_baseline` 跑通 `train -> val -> eval`。

## 后置内容

下面这些内容保留为后续方向，但不再作为 v1 的执行前提：

- 闭环环境。
- `patch` DSL。
- 观测 schema。
- Checker / Router / DRC 联动。
- 强化学习式交互循环。

## 当前约束

- 第一阶段唯一主任务是 `LocalRouteChoice-Lite`。
- `DeepSeek-VL` 与 `Janus` 仅是实验后端接口占位。
- 正式实现顺序以最小训练闭环优先，而不是环境模块优先。
