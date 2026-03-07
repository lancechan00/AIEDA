# 动作协议 (Patch Format DSL)

## 1. 概述

`Patch` 是本项目中模型 (Policy) 与环境 (Environment) 交互的**唯一语言**。模型不直接修改 PCB 文件，而是输出一个 `Patch` 对象，描述对当前板卡状态的增量修改。

## 2. Patch 核心 Schema

推荐使用 JSON/YAML 格式作为中间表示，在代码中对应 `src/schemas/patch.py`。

### 基础结构
```json
{
  "version": "v1",
  "timestamp": "2026-03-07T...",
  "op": "add_trace | add_via | remove_item | modify_item",
  "net_id": "NET_01",
  "params": { ... }
}
```

## 3. 支持的操作类型 (Operations)

### A. add_trace (添加走线)
用于在指定层添加一段或多段走线。
- **params**:
  - `layer`: 目标层 (如 "F.Cu", "B.Cu")。
  - `points`: 坐标序列 `[[x1, y1], [x2, y2], ...]`。
  - `width`: 线宽 (可选，默认使用 Net Class 规则)。
  - `mode`: "direct" (直线) | "ortho" (直角) | "45degree" (45度)。

### B. add_via (添加过孔)
用于在指定位置添加换层过孔。
- **params**:
  - `at`: 坐标 `[x, y]`。
  - `layers`: 跨越层 `["F.Cu", "B.Cu"]`。
  - `drill`: 孔径 (可选)。

### C. remove_item (删除元素)
用于撤销或删除已有的走线段或过孔。
- **params**:
  - `item_id`: 元素唯一标识。

## 4. 为什么使用 Patch 模式？

1. **可校验性**: 在真正写入板卡前，`Checker` 可以对 `Patch` 进行静态检查。
2. **可逆性**: 方便实现 `Undo/Redo`，支持强化学习中的回溯搜索。
3. **解耦**: 模型不需要了解 KiCad 的底层文件格式，只需理解 `Patch` 语义。
4. **引导性**: `Router` 可以根据 `Patch` 中的粗略 `points` (Waypoints) 进行 A* 路径补全。

## 5. 示例：模型输出的一个 Patch

```json
{
  "op": "add_trace",
  "net_id": "VCC_3V3",
  "params": {
    "layer": "F.Cu",
    "points": [[10.5, 20.0], [15.0, 20.0], [15.0, 25.5]],
    "width": 0.25
  }
}
```
