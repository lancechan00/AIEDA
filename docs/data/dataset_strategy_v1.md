# 数据获取与处理计划 (Data Pipeline)

## 1. 数据获取策略 (Data Ingestion)

### 核心源：开源 KiCad 项目
优先从 GitHub 获取高质量、可解析的 KiCad PCB 项目。
- **筛选标准**: 
  - Stars > 10
  - 包含 `.kicad_pcb` 和 `.net` 文件。
  - 层数：2-4 层（首版聚焦）。
  - 复杂度：10-200 个元件。

### 存储结构 (`data/`)
```text
data/
├── raw/                # 原始 KiCad 项目文件
├── interim/            # 解析后的中间格式 (JSON/Pickle)
│   ├── boards/         # 板卡物理信息
│   ├── graphs/         # 网络拓扑图
│   └── geometry/       # 几何栅格数据
└── processed/          # 最终训练样本 (train/val/test)
```

## 2. 样本构造 (Sample Construction)

由于完整布线过于复杂，首版采用**“局部样本提取”**策略：
- **目标**: 提取以特定 Net 或 Pin 为中心的局部区域 (e.g., 64x64 grid)。
- **输入模态**:
  - **Geometry Tensor**: 包含占用、层、引脚、障碍物的多通道栅格。
  - **Graph Features**: 局部网络拓扑。
  - **Text Rules**: 对应的线宽、间距规则。
- **输出**: 对应的布线 Patch (从已有成品板反推)。

## 3. 标注策略 (Annotation)

v1 阶段不进行大规模人工标注，采用**程序化弱标注 (Weak Supervision)**：
1. **反推 Patch**: 从完成的 PCB 中，随机去掉一段走线，将“恢复该走线”作为动作标签。
2. **方向偏好**: 基于几何分析，标注局部区域的布线推荐方向。
3. **拥塞评分**: 自动计算区域布线难度，作为辅助训练信号。

## 4. 数据管道流程

1. `scripts/download_data.sh`: 从 GitHub 批量拉取项目。
2. `src/data_pipeline/ingest/parse_kicad.py`: 解析 S-Expression 格式。
3. `src/data_pipeline/transform/board_to_grid.py`: 生成几何张量。
4. `src/data_pipeline/build_dataset.py`: 提取样本并划分数据集。
