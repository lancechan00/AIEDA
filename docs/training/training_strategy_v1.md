# 训练策略 (Training Strategy V1)

## 1. 首版训练定位

v1 的目标不是先证明“小模型能不能做”，而是验证**主流多模态大模型技术栈**在 PCB 任务上的适配方式是否成立。为此，首版保留大模型后端、统一适配层、多模态输入和结构化输出协议；同时把可简化环节用 `mock`、弱标注和轻量环境替代。

## 2. 三阶段训练路线

### 第一阶段：监督学习 / 模仿学习 (Supervised/Imitation)
- **目标**: 让模型学会“像人类一样布线”。
- **数据**: 从开源 PCB 反推的 `(State, Patch)` 对。
- **后端定位**: 优先接入 `DeepSeek-VL`、`Janus` 或同类主流多模态模型，通过适配层完成训练/推理接口统一。
- **损失函数**: 
  - Patch 序列的交叉熵损失。
  - 坐标预测的均方误差 (MSE)。

### 第二阶段：环境闭环微调 (In-Environment Fine-tuning)
- **目标**: 提高 Patch 的物理合法性和成功率。
- **方法**: 
  - 模型输出 Patch -> 环境执行 -> DRC 反馈。
  - 使用强化学习 (如 PPO) 或 拒绝采样 (Rejection Sampling) 进行微调。
  - 首版允许 `mock router`、`mock patch executor`、弱 DRC 近似器参与反馈环路，只要接口与后续真实模块保持一致。
- **奖励函数**: `R = w1 * Success + w2 * (-DRC_Violations) + w3 * (-Path_Length)`。

### 第三阶段：扩散先验集成 (Diffusion Prior Integration)
- **目标**: 引入全局规划能力。
- **方法**: 
  - 训练一个扩散模型生成“拥塞热图”或“推荐走线走廊”。
  - 将此热图作为额外的 Observation 通道输入给 Policy 模型。

## 3. 模态验证实验 (Modality Validation)

为了确定最优输入组合，需进行消融实验：
- **Exp 1**: 仅几何张量 (Geometry Only)。
- **Exp 2**: 几何 + 图特征 (Geometry + Graph)。
- **Exp 3**: 几何 + 图 + 规则文本 (Geometry + Graph + Text)。
- **指标**: 预测 Patch 与真实路径的重合度、DRC 通过率。

## 4. 模型后端选择

- **Primary**: 主流多模态大模型后端，如 `DeepSeek-VL`、`Janus`，用于验证技术栈适配性。
- **Support Baseline**: 轻量模型或规则模型，仅用于对照实验和接口回归测试，不作为 v1 主叙事。
- **Adapter Layer**: 统一封装 tokenizer / processor / multimodal input packing / structured output parsing，保证不同大模型后端可横向比较。

## 5. Mock 策略

- **Mock 数据标签**: 用弱标注、反推 Patch、程序化样本代替大规模人工标注。
- **Mock 环境反馈**: 用简化版 Checker / DRC / Router 保持闭环可运行。
- **Mock 输出约束**: 允许先预测简化 `Patch DSL`，但输出协议必须与正式版本兼容。
- **不 Mock 的部分**: 大模型后端接入方式、多模态输入组织方式、结构化输出协议、实验比较框架。

## 6. 评估指标 (Evaluation)

- **布线完成率 (Completion Rate)**: 成功连接的网络比例。
- **DRC 违规数 (DRC Violations)**: 每单位面积的违规次数。
- **线长效率 (Wirelength Efficiency)**: 实际线长与曼哈顿距离的比值。
- **过孔密度 (Via Density)**: 换层频率。
