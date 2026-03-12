# AIEDA 项目路线图（v1）

**日期**：2026-03-12

---

## 1. 整体方向

项目沿**多模态技术路线**推进：训练合适的多模态模型，串联成可对话的 Agent，最终形成 **PCB 画线 Agent**。原理图级别 Agent 期待由社区或协作方实现，形成 PCB + 原理图 的完整设计链。

---

## 2. 阶段划分

| 阶段 | 重心 | 产出 |
|------|------|------|
| **第一阶段** | 模态与训练可行性验证 | LocalRouteChoice-Lite 跑通；geometry/image 消融；弱标注闭环 |
| **第二阶段** | 多模态模型成型 | GraphEncoder + Qwen3-VL-Embedding 等对齐；检索、Patch 生成稳定 |
| **第三阶段** | Agent 串联 | 大模型 + 模态 + EDA 环境语义连接 → PCB 画线 Agent |
| **延伸** | 原理图 Agent | 期待社区/协作方实现，与本项目 PCB Agent 形成上下游 |

---

## 3. PCB 画线 Agent 愿景

将当前技术栈稳定后，串联为 **PCB 画线 Agent**：

1. **多模态模型**：GraphEncoder、Qwen embedding/VL-Embedding 等，把 graph、geometry、image 映射到统一语义空间
2. **大模型**：负责推理、生成、自然语言交互
3. **EDA 环境语义**：与 KiCad 等工具深度连接，获取选区、设计状态、DRC 结果等
4. **自然对话**：用户用自然语言提问（如「这条线路走得怎么样？」），Agent 结合模态理解与环境状态，给出语义化回答

核心能力：
- 「这条线路走得怎么样？」→ 检索相似设计 + 规则检查 → 给出评价与建议
- 「这块区域有什么问题？」→ 结合 DRC、信号完整性等
- 「帮我优化这一段」→ 检索 + 生成 Patch + 通过 EDA 接口应用

---

## 4. 分工预期

| 范围 | 责任方 | 说明 |
|------|--------|------|
| **PCB 画线 Agent** | 本项目 | 多模态模型 + 大模型 + EDA 环境 → 画线辅助、对话理解 |
| **原理图 Agent** | 社区 / 协作方 | 原理图级理解与辅助，与本项目形成设计链上下游 |

---

## 5. 关联文档

- 第一阶段目标：`docs/overview/project_goal.md`
- 架构与约束：`docs/overview/architecture_v1.md`
- 多模态 embedding 考量：`docs/training/memo_multimodal_embedding_v1.md`
- 决策日志：`docs/overview/decision_log_v1.md`
