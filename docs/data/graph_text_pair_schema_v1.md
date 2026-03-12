# Graph-Text 样本格式（v1）

## 任务定义

第一阶段任务固定为 `GraphTextRetrieval`：

- 输入：PCB 图统计特征 `graph_features` + 文本描述 `text`
- 目标：正确图文配对在向量空间中更近，错误配对更远

## 文件布局

```text
data/embedding/graph_text_pairs/
  dataset_summary.json
  train/
    data.jsonl
    metadata.json
  val/
    data.jsonl
    metadata.json
  test/
    data.jsonl
    metadata.json
```

## `data.jsonl` 单条样本

```json
{
  "sample_id": "board_alpha_0",
  "task_type": "GraphTextRetrieval",
  "board_id": "board_alpha",
  "text": "Board board_alpha has 0 components, 1 nets, 2 tracks, 0 vias and 1 layers.",
  "graph_features": [0.0, 2.0, 0.0, 1.0, 1.0, 12.0, 0.25, 0.0, 0.0, 1.0, 1.0, 0.0],
  "hard_negatives": [
    "Board board_beta has 1 components, 2 nets, 4 tracks, 1 vias and 2 layers."
  ],
  "metadata": {
    "source_project": "board_alpha",
    "text_type": "board_summary"
  }
}
```

## `graph_features` 维度约定

固定 12 维，顺序不可变：

1. `num_components`
2. `num_tracks`
3. `num_vias`
4. `num_nets`
5. `num_layers`
6. `avg_track_length`
7. `avg_track_width`
8. `avg_via_size`
9. `power_net_ratio`
10. `signal_net_ratio`
11. `top_layer_track_ratio`
12. `bottom_layer_track_ratio`

## 正负样本策略

- 正样本：同一板的 `graph_features` 与该板摘要文本/网络文本/路径属性文本。
- 硬负样本：从其他样本文本池随机抽取，不等于当前正样本文本。
- 第一阶段默认 `negatives_per_sample=2`，可按显存调节。

## 构建命令

```powershell
python .\apps\data_cli.py build-pairs --parsed-dir .\data\embedding\parsed --output-dir .\data\embedding\graph_text_pairs --seed 7 --negatives-per-sample 2
```
