# PCB 环境与闭环 (PCB Environment)

## 1. 模块定义

PCB 环境 (`Environment`) 是一个模拟器，它维护板卡的当前物理状态 (`Board State`)，并提供标准的强化学习接口：`step()`, `reset()`, `render()`。

## 2. Board State (板卡状态)

`Board State` 负责管理内存中的 PCB 几何数据，不直接操作磁盘文件。

### 核心组件：
- **Geometry Database**: 存储焊盘 (Pads)、走线 (Traces)、过孔 (Vias)、禁布区 (Keepouts) 的空间索引 (R-Tree)。
- **Connectivity Graph**: 维护网络 (Nets) 与引脚 (Pins) 的连接状态。
- **Rule Book**: 存储设计规则 (DRC Rules)，如最小间距、最小线宽。

## 3. 执行流程 (The `step` function)

当调用 `env.step(patch)` 时，发生以下过程：

1. **Pre-Check (Checker)**: 
   - 检查 `net_id` 是否存在。
   - 检查坐标是否在板框内。
   - 检查操作是否符合基本逻辑（如不能在没有焊盘的地方起线）。
2. **Execution (Apply)**:
   - 将 `Patch` 中的几何元素尝试加入 `Geometry Database`。
3. **Validation (DRC & Router)**:
   - **DRC**: 检查新加入的元素是否导致短路 (Short) 或间距违规 (Clearance Violation)。
   - **Router**: 如果 `Patch` 是粗略路径，调用启发式 Router 进行精细化补全。
4. **State Update**:
   - 更新连通性状态。
   - 计算当前分值 (Reward)。
5. **Return**:
   - 返回 `Observation`, `Reward`, `Done`, `Info` (含错误详情)。

## 4. 关键子模块职责

### Checker (校验器)
- **定位**: 低成本过滤器。
- **任务**: 拦截明显错误的动作，避免浪费昂贵的 DRC 计算资源。

### DRC (设计规则检查)
- **定位**: 物理合法性底线。
- **首版指标**:
  - **Clearance**: 走线与走线、走线与焊盘的间距。
  - **Short**: 不同网络之间的电气接触。
  - **Boundary**: 是否超出板框。

### Evaluator (评估器)
- **任务**: 对当前局面打分。
- **指标**: 
  - 布线完成率 (Completion Rate)。
  - 总线长 (Total Wire Length)。
  - 过孔数量 (Via Count)。
  - DRC 违规密度。

## 5. MCP 接口建议

为了方便外部 Agent (如 Cursor/Claude) 调试，环境应暴露以下 MCP 工具：
- `apply_patch(patch)`: 执行动作并返回结果。
- `get_board_snapshot()`: 返回当前板卡的视觉/几何快照。
- `run_full_drc()`: 运行完整物理检查并返回违规列表。
