# KiCad 数据计划

第一阶段的数据目标不是做大，而是做真、做稳、做可复现。

## 数据源

- 主输入：`.kicad_pcb`
- 可选补充：`.net`

当前实现不再强依赖 `.net`；如果缺失，就从 PCB 内部 net 信息退化生成最小 netlist。

## 样本构造

从真实板子的 `track segment` 构造 `LocalRouteChoice-Lite` 样本：

1. 读取板级 JSON。
2. 遍历真实 segment。
3. 在 segment 起点附近提取局部窗口。
4. 用真实终点方向生成弱标注。

## 数据切分

严格采用 `board-level` 划分：

- 一块板子的样本只能属于一个 split。
- 不做样本级随机切分。

## 仓库自带 fixture

仓库当前内置：

- `data/fixtures/parsed_boards/`
- `data/fixtures/local_route_choice_lite/`

用途：

- 快速验证数据构建链。
- 在 Windows 环境跑通 `train -> val -> eval`。
- 作为 smoke test 固定基准。
