# v1 训练任务

第一阶段只保留一个任务：

`LocalRouteChoice-Lite`

## 任务定义

给定一个局部走线窗口，预测被遮蔽掉的下一段主方向。

## 输入

- `geometry`: `64 x 64 x 4`
- `image`: 与局部几何对齐的 RGB 图

当前四个几何通道为：

1. 其他走线占用。
2. 同 net 上下文占用。
3. 当前起点 marker。
4. 当前目标点 marker。

## 输出

五分类：

- `up`
- `down`
- `left`
- `right`
- `stop`

## 标签来源

标签来自真实 KiCad 走线的确定性弱标注：

1. 读取一个真实 `track segment`。
2. 以 segment 起点构造局部窗口。
3. 用 segment 的真实终点方向生成分类标签。
4. 不使用随机 mock 标签。

## 切分规则

数据按 `board-level` 划分：

- `train`
- `val`
- `test`

同一块板子的样本不能跨 split 出现。

## 指标

- `accuracy`
- `top-3 accuracy`

## 后端角色

- `tiny_baseline`: 正式训练后端。
- `DeepSeek-VL`: 同任务实验接口，占位为推理后端。
- `Janus`: 同任务实验接口，占位为推理后端。

## 当前不做

- `NetRegionMatch`
- `MockPatchPrediction`
- 多任务联合训练
- patch 序列训练
