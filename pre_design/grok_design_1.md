可以。你现在最需要的不是继续发散，而是把项目**压成一个可研发、可迭代、可测试**的工程骨架。

我给你两样东西：

1. 一份适合你当前阶段的**研发目录结构**
2. 一份**重点突破模块说明**，覆盖模型、数据、训练、输入输出、checker/router/DRC/状态编码器的职责与首版技术选择

我会按“**首版能跑**”优先，不按“终局最强”来设计。

---

# 一、先给你一个结论版

你的项目建议拆成 5 个层：

* **docs**：设计文档、路线图、实验记录
* **data**：样本、转换后的中间数据、训练集
* **models**：多模态策略模型、可选扩散先验模型
* **engine**：PCB 环境，含 checker/router/DRC/legalizer/state
* **runtime**：服务、编排、测试、评测、demo

你的首版目标不要做成“大而全平台”，而要做成：

> **一个能跑闭环的 research prototype**
>
> 输入：board state + netlist + rules
> 输出：diff/patch
> 环境执行并反馈 observation

---

# 二、推荐研发目录结构

下面这个结构适合你现在的方向，既能放研究文档，也能放训练、服务和测试。

```text
pcb-ai-router/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
│
├── docs/
│   ├── 00_overview/
│   │   ├── project_goal.md
│   │   ├── scope_and_boundary.md
│   │   ├── architecture_v1.md
│   │   ├── architecture_v2.md
│   │   └── glossary.md
│   │
│   ├── 01_research/
│   │   ├── problem_formulation.md
│   │   ├── model_options_llm_multimodal_diffusion.md
│   │   ├── routing_as_sequential_decision.md
│   │   ├── state_action_reward_design.md
│   │   └── risks_and_open_questions.md
│   │
│   ├── 02_modules/
│   │   ├── policy_model.md
│   │   ├── diffusion_prior.md
│   │   ├── pcb_environment.md
│   │   ├── checker.md
│   │   ├── router.md
│   │   ├── drc.md
│   │   ├── legalizer.md
│   │   ├── state_encoder_geometry.md
│   │   ├── state_encoder_graph.md
│   │   ├── patch_format.md
│   │   └── evaluator.md
│   │
│   ├── 03_data/
│   │   ├── dataset_plan.md
│   │   ├── raw_data_sources.md
│   │   ├── data_schema.md
│   │   ├── preprocessing.md
│   │   ├── annotation_spec.md
│   │   └── train_val_test_split.md
│   │
│   ├── 04_training/
│   │   ├── training_strategy_v1.md
│   │   ├── supervised_finetune.md
│   │   ├── imitation_learning.md
│   │   ├── rl_plan_future.md
│   │   ├── loss_design.md
│   │   └── experiment_matrix.md
│   │
│   ├── 05_system/
│   │   ├── api_contracts.md
│   │   ├── service_topology.md
│   │   ├── runtime_loop.md
│   │   ├── mcp_integration_notes.md
│   │   └── deployment_plan.md
│   │
│   └── 06_logs/
│       ├── decisions.md
│       ├── weekly_notes.md
│       └── experiment_journal.md
│
├── data/
│   ├── raw/
│   │   ├── kicad_projects/
│   │   ├── pcb_files/
│   │   ├── netlists/
│   │   ├── screenshots/
│   │   └── rules/
│   │
│   ├── interim/
│   │   ├── parsed_boards/
│   │   ├── parsed_graphs/
│   │   ├── geometry_maps/
│   │   ├── patches/
│   │   └── metadata/
│   │
│   ├── processed/
│   │   ├── train/
│   │   ├── val/
│   │   ├── test/
│   │   └── benchmarks/
│   │
│   └── sample_cases/
│       ├── tiny/
│       ├── simple_2layer/
│       └── diffpair_cases/
│
├── configs/
│   ├── model/
│   │   ├── policy_v1.yaml
│   │   ├── policy_v2_multimodal.yaml
│   │   └── diffusion_prior_v1.yaml
│   │
│   ├── env/
│   │   ├── board_rules_default.yaml
│   │   ├── router_default.yaml
│   │   └── drc_default.yaml
│   │
│   ├── training/
│   │   ├── sft_v1.yaml
│   │   ├── imitation_v1.yaml
│   │   └── ablation_v1.yaml
│   │
│   └── runtime/
│       ├── local_dev.yaml
│       ├── api_dev.yaml
│       └── eval.yaml
│
├── src/
│   ├── common/
│   │   ├── logging.py
│   │   ├── paths.py
│   │   ├── utils.py
│   │   ├── registry.py
│   │   └── types.py
│   │
│   ├── schemas/
│   │   ├── board.py
│   │   ├── netlist.py
│   │   ├── patch.py
│   │   ├── observation.py
│   │   ├── action.py
│   │   ├── drc.py
│   │   └── metrics.py
│   │
│   ├── data_pipeline/
│   │   ├── ingest/
│   │   │   ├── parse_kicad.py
│   │   │   ├── parse_netlist.py
│   │   │   └── parse_rules.py
│   │   │
│   │   ├── transform/
│   │   │   ├── board_to_graph.py
│   │   │   ├── board_to_grid.py
│   │   │   ├── board_to_image.py
│   │   │   ├── route_to_patch.py
│   │   │   └── patch_to_board.py
│   │   │
│   │   ├── build_dataset.py
│   │   └── validate_dataset.py
│   │
│   ├── environment/
│   │   ├── board_state.py
│   │   ├── env.py
│   │   ├── step.py
│   │   ├── action_mask.py
│   │   ├── reward.py
│   │   └── done.py
│   │
│   ├── encoders/
│   │   ├── geometry/
│   │   │   ├── occupancy_map.py
│   │   │   ├── layer_map.py
│   │   │   ├── pin_map.py
│   │   │   └── congestion_map.py
│   │   │
│   │   ├── graph/
│   │   │   ├── net_graph.py
│   │   │   ├── component_graph.py
│   │   │   └── heterogeneous_graph.py
│   │   │
│   │   └── observation_builder.py
│   │
│   ├── engine/
│   │   ├── checker/
│   │   │   ├── connectivity_checker.py
│   │   │   ├── rule_checker.py
│   │   │   └── patch_checker.py
│   │   │
│   │   ├── router/
│   │   │   ├── astar_router.py
│   │   │   ├── maze_router.py
│   │   │   ├── pattern_router.py
│   │   │   └── ripup_reroute.py
│   │   │
│   │   ├── drc/
│   │   │   ├── clearance.py
│   │   │   ├── width.py
│   │   │   ├── via_rules.py
│   │   │   └── diffpair_rules.py
│   │   │
│   │   ├── legalizer/
│   │   │   ├── snap_to_grid.py
│   │   │   ├── corner_cleaner.py
│   │   │   └── via_adjuster.py
│   │   │
│   │   └── evaluator/
│   │       ├── route_metrics.py
│   │       ├── congestion_metrics.py
│   │       └── score.py
│   │
│   ├── models/
│   │   ├── policy/
│   │   │   ├── base.py
│   │   │   ├── multimodal_policy_v1.py
│   │   │   ├── heads/
│   │   │   │   ├── net_select_head.py
│   │   │   │   ├── waypoint_head.py
│   │   │   │   ├── layer_head.py
│   │   │   │   └── via_head.py
│   │   │   └── decoder_patch.py
│   │   │
│   │   ├── prior/
│   │   │   ├── diffusion_prior_v1.py
│   │   │   ├── heatmap_decoder.py
│   │   │   └── corridor_prior.py
│   │   │
│   │   └── adapters/
│   │       ├── hf_multimodal_adapter.py
│   │       └── vision_encoder_adapter.py
│   │
│   ├── training/
│   │   ├── sft/
│   │   │   ├── train_policy.py
│   │   │   ├── dataset.py
│   │   │   └── collator.py
│   │   │
│   │   ├── imitation/
│   │   │   ├── train_imitation.py
│   │   │   └── rollout_dataset.py
│   │   │
│   │   ├── rl/
│   │   │   ├── train_rl.py
│   │   │   └── buffer.py
│   │   │
│   │   └── losses/
│   │       ├── patch_loss.py
│   │       ├── route_success_loss.py
│   │       └── prior_alignment_loss.py
│   │
│   ├── runtime/
│   │   ├── orchestrator.py
│   │   ├── inference_loop.py
│   │   ├── task_runner.py
│   │   └── session_manager.py
│   │
│   ├── services/
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   ├── routes.py
│   │   │   └── deps.py
│   │   │
│   │   ├── worker/
│   │   │   ├── job_worker.py
│   │   │   └── queue.py
│   │   │
│   │   └── mcp/
│   │       ├── server.py
│   │       ├── tools/
│   │       │   ├── run_drc.py
│   │       │   ├── apply_patch.py
│   │       │   ├── export_board.py
│   │       │   └── render_snapshot.py
│   │       └── resources/
│   │           └── board_state_resource.py
│   │
│   └── ui/
│       ├── cli.py
│       └── simple_viewer.py
│
├── scripts/
│   ├── download_open_data.sh
│   ├── build_dataset.sh
│   ├── train_policy.sh
│   ├── run_local_demo.sh
│   ├── eval_benchmark.sh
│   └── export_case.sh
│
├── tests/
│   ├── unit/
│   │   ├── test_patch_schema.py
│   │   ├── test_board_state.py
│   │   ├── test_router_astar.py
│   │   ├── test_drc_clearance.py
│   │   └── test_observation_builder.py
│   │
│   ├── integration/
│   │   ├── test_env_step.py
│   │   ├── test_patch_apply_and_check.py
│   │   ├── test_policy_loop.py
│   │   └── test_export_import.py
│   │
│   └── e2e/
│       ├── test_small_board_demo.py
│       └── test_simple_2layer_case.py
│
├── outputs/
│   ├── runs/
│   ├── checkpoints/
│   ├── predictions/
│   ├── reports/
│   └── visualizations/
│
└── notebooks/
    ├── 00_data_inspection.ipynb
    ├── 01_board_to_graph.ipynb
    ├── 02_observation_debug.ipynb
    ├── 03_patch_debug.ipynb
    └── 04_eval_analysis.ipynb
```

---

# 三、这个目录里，哪些是你现在最先该建的

先不要全建。第一批先建这 12 个：

```text
docs/
docs/00_overview/
docs/02_modules/
data/raw/
data/interim/
configs/
src/schemas/
src/data_pipeline/
src/environment/
src/encoders/
src/engine/
src/models/
tests/
```

第一周内最重要的是把这几个文件先写出来：

* `docs/00_overview/project_goal.md`
* `docs/00_overview/architecture_v1.md`
* `docs/02_modules/patch_format.md`
* `docs/02_modules/pcb_environment.md`
* `docs/02_modules/state_encoder_geometry.md`
* `docs/02_modules/state_encoder_graph.md`
* `src/schemas/patch.py`
* `src/schemas/board.py`
* `src/environment/env.py`
* `src/encoders/observation_builder.py`

---

# 四、重点突破模块文档

下面这部分，你可以直接当成项目设计文档初稿。

---

## 1. 模型主干：为什么先选开源多模态模型

### 目标

不是让模型直接“画 PCB 图”，而是让模型做：

* 读 observation
* 理解 net 语义和空间状态
* 输出结构化 patch

### 为什么不是纯 LLM

因为输入不只是文本，而是：

* 板上几何状态
* netlist 图关系
* 可选规则文本
* 历史 patch

### 为什么不是纯扩散

因为你的最终输出要进入 EDA，必须结构化；扩散更适合做全局先验，不适合首版直接做最终动作。

### 首版建议

用一个**轻量多模态策略模型**，而不是追求最强大模型。

更准确地说：

> 首版不是“拿一个现成大多模态模型端到端跑”
>
> 而是“用现成视觉编码器 + 图/结构编码 + 自定义 patch head”

---

## 2. 模型训练核心思路

### 第一阶段：监督微调 / 模仿学习

目标是学习：

* 在给定 state 下，应该选哪个 net
* 应该走什么粗路径
* 应该是否换层
* 应该产出怎样的 patch

训练样本形式：

```text
input:
  board_state
  pending_nets
  rules
  optional image/grid/graph

target:
  patch/diff
```

### 第二阶段：环境闭环训练

把模型放入环境里：

* 模型输出 patch
* 环境执行
* checker/router/DRC 反馈
* 用成功率、DRC 违规数、线长、via 数做奖励或辅助损失

### 第三阶段：扩散先验加入

扩散不直接出 patch，而是输出：

* congestion heatmap
* corridor prior
* layer preference map

然后作为 observation 一部分输入 policy。

---

## 3. 开源数据库建议

### 首版简单选择

优先找**可解析的 KiCad / 开源 PCB 工程**，不要一开始追求大而全。

你要的数据不是“最终图片”，而是：

* 板子文件
* 元件位置
* pad 坐标
* netlist
* trace
* layer
* rules

### 你真正需要的数据形式

你要把原始工程转成三类中间数据：

#### A. 图结构

* component graph
* pin-net graph
* route graph

#### B. 几何状态

* occupancy map
* pin map
* trace mask
* via map
* layer map

#### C. patch 序列

把已有完整板反推出“逐步 patch 序列”
这是最重要也最难的一个数据工程点。

### 首版建议

先做小数据集：

* 单/双层板
* 低 pin count
* 无高速复杂差分
* 先忽略模拟精细约束

---

## 4. 输入输出处理建议

### 模型输入

建议做成 hybrid：

#### 输入 1：geometry tensor

例如每层若干通道：

* board boundary
* pads
* occupied traces
* blocked area
* pending target pins
* congestion map

#### 输入 2：graph features

* net graph
* component graph
* 当前未完成 nets
* net priority/type

#### 输入 3：rule tokens

* width class
* clearance class
* diff pair flag
* power / signal type

#### 输入 4：history

* 最近若干 patch
* 已完成率
* 当前 score

---

### 模型输出

首版不要直接输出整条复杂 polyline，可以分层：

#### 版本 A：粗动作

* select_net
* target_layer
* route_mode
* place_via yes/no

#### 版本 B：中等 patch

* 一条短 polyline 段
* 或一个 waypoint

#### 版本 C：完整 patch DSL

推荐你自己定义一个中间格式：

```text
PATCH {
  op: "add_trace"
  net: "NET_12"
  layer: "top"
  points: [[120,40],[140,40],[140,80]]
  width: 0.2
}
```

首版强烈建议输出这个，不要直接操作原始 EDA 文件。

---

# 五、每个环境模块的意义、首版技术选择、后续增强

---

## 1. checker

### 存在意义

checker 是“低成本过滤器”，负责判断 patch 是否基本可执行，避免模型频繁产出荒谬动作。

### 它检查什么

* net 是否存在
* 点序列是否合法
* 起点终点是否在合理范围
* patch 是否越界
* patch 是否明显冲突

### 首版简单选择

自己写，基于 patch schema + board state 做静态检查。

### 后续增强

加入更多 rule-aware 检查。

---

## 2. router

### 存在意义

router 不是替代模型，而是：

* 帮模型把粗动作落到精确路径
* 或在模型失败时兜底

### 首版简单选择

A* / maze router 二选一即可。

### 后续增强

* rip-up and reroute
* pattern routing
* 多层 cost routing

---

## 3. DRC

### 存在意义

DRC 是工程合法性的底线，不可缺。

### 检查内容

* clearance
* width
* via rule
* short/open
* layer constraints

### 首版简单选择

只做 4 个最基本：

* 越界
* 短路
* 间距
* 线宽

### 后续增强

* diff pair
* length match
* power class
* keepout

---

## 4. 状态编码器（geometry）

### 存在意义

把“板子的空间局面”编码给模型。
这是你说的“空间直觉”的主要来源。

### 首版输入建议

输出固定大小 grid tensor：

* pads mask
* occupied mask
* target net mask
* obstacle mask
* board mask

### 首版技术规范

先做 2D 栅格，不做复杂矢量。

### 后续增强

* 多层分通道
* congestion channel
* route history channel
* diffusion prior channel

---

## 5. 状态编码器（graph）

### 存在意义

geometry 解决“哪里能走”，graph 解决“该走谁、为什么”。

### 编码内容

* net-to-pin
* component-to-pin
* pending nets
* net classes
* priority
* route completion ratio

### 首版简单选择

先不用复杂 GNN，先把 graph 特征整理成结构化表征喂给 MLP/Transformer head。

### 后续增强

引入 heterogeneous GNN。

---

# 六、首版技术选型建议

---

## A. 深度报告版（理想路线）

适合文档论证与中长期演化。

### 模型

* 多模态策略模型
* 几何编码器 + 图编码器 + patch decoder
* 可选扩散先验生成拥塞热图

### 训练

* 先监督微调
* 再 imitation rollout
* 最后 RL / search

### 环境

* 自研 PCB 环境
* patch apply + checker + router + DRC + evaluator

### 输出

* 中间 patch DSL
* translator 转为 EDA 文件修改

---

## B. 首版简单选择

这是我更推荐你马上做的。

### 模型

* 不直接依赖超大开源多模态模型
* 用：

  * 小型视觉编码器
  * 简单 graph feature encoder
  * MLP/Transformer decoder 输出 patch

### 环境

* Python 自研 board state
* A* router
* 4 项基础 DRC
* patch apply / undo

### 数据

* 小规模开源 KiCad case
* 人工/程序生成 patch 样本

### 输出

* 自定义 patch JSON
* 一个 translator 转成板状态，不急着直接写 KiCad 文件

这条路线最稳。

---

# 七、MCP 版本建议

如果你说的 MCP 是把系统工具化暴露给模型或外部编排层，那么建议是：

### 首版不要把 MCP 当核心

首版用纯 Python 接口更快。

### 什么时候加 MCP

当你要：

* 让外部 agent 调 DRC
* 让外部工具读 board state
* 让 UI、服务、调试脚本统一调用时

再加一个轻量 MCP server。

### MCP 首版只暴露 4 个工具

* `apply_patch`
* `run_drc`
* `get_board_state`
* `render_snapshot`

这样最干净。

---

# 八、你现在最该写的 8 份文档

我建议你先把这些写出来，别急着写太多代码：

1. `docs/00_overview/project_goal.md`
2. `docs/00_overview/architecture_v1.md`
3. `docs/01_research/problem_formulation.md`
4. `docs/02_modules/patch_format.md`
5. `docs/02_modules/pcb_environment.md`
6. `docs/02_modules/state_encoder_geometry.md`
7. `docs/02_modules/state_encoder_graph.md`
8. `docs/04_training/training_strategy_v1.md`

---

# 九、一个最小可行里程碑

## M0：文档和 schema

* patch schema
* board schema
* env loop 文档

## M1：环境闭环

* board state
* apply patch
* checker
* 简单 router
* 基础 DRC

## M2：无模型 baseline

* heuristic policy
* 跑通小板子

## M3：小模型 policy

* 输入 observation
* 输出 patch

## M4：评测

* 成功率
* 违规数
* 线长
* via 数
* 完成率

---

如果你愿意，下一步我可以直接帮你继续落地两件最实用的东西之一：

要么我给你写出
**`docs/00_overview/architecture_v1.md` 的完整初稿**

要么我直接给你写
**`patch.py / board.py / observation.py` 三个核心 schema 的设计草案**。
