# 模态候选方案

## 概述

PCB 布线任务涉及多种信息模态的整合。本文档定义了 v1 阶段需要验证的输入模态及其优先级组合。

## 核心模态候选

### 1. 几何栅格 (Geometry Grid) - 优先级: 高

#### 描述
将 PCB 板子的物理空间表示为 2D/3D 栅格，每个栅格点包含：
- 占用状态 (occupied/free)
- 层信息 (layer id)
- 引脚位置 (pin locations)
- 走线通道 (routing channels)

#### 技术实现
- **格式**: 3D numpy array 或 torch tensor
- **维度**: [height, width, channels]
- **通道**: occupancy, layer_mask, pin_density, congestion_heatmap
- **分辨率**: 建议从 32x32 开始，逐步到 128x128

#### 优势
- 结构化表示，易于神经网络处理
- 直接反映空间约束和布线可能性
- 计算效率高

#### 适用任务
- LocalRouteChoice: 预测局部区域的可布线方向
- NetRegionMatch: 计算 net 与几何区域的匹配度

### 2. 板图图像 (Board Image) - 优先级: 高

#### 描述
PCB 设计的视觉截图或渲染图，包含：
- 元件布局和引脚位置
- 已有的走线轨迹
- 层叠加信息
- DRC 违规标记（可选）

#### 技术实现
- **格式**: RGB/RGBA 图像
- **分辨率**: 224x224 或 512x512
- **预处理**: 标准化、数据增强（旋转、缩放）
- **编码器**: ViT, CNN, 或直接输入多模态模型

#### 优势
- 直观反映设计状态
- 利用成熟的视觉模型能力
- 易于人类理解和调试

#### 适用任务
- LocalRouteChoice: 基于视觉线索预测布线方向
- MockPatchPrediction: 视觉引导的动作生成

### 3. 文本规则 (Text Rules) - 优先级: 中

#### 描述
PCB 设计规范和约束的文本化表示：
- DRC 规则 (clearance, width, via rules)
- 设计约束 (layer restrictions, net classes)
- 布线偏好 (preferred directions, routing styles)

#### 技术实现
- **格式**: 结构化文本或 token 序列
- **编码**: BERT-style 文本编码器或大模型的文本输入
- **长度**: 限制在 512 tokens 以内

#### 优势
- 精确表达设计意图和约束
- 易于规则更新和定制
- 支持条件推理

#### 适用任务
- 作为辅助输入增强其他模态
- MockPatchPrediction: 规则引导的决策

### 4. 图结构 (Graph Structure) - 优先级: 中

#### 描述
Netlist 的图论表示：
- **节点**: 元件引脚 (pins), 连接点 (junctions)
- **边**: 电气连接 (nets), 空间邻接 (adjacency)
- **属性**: 引脚坐标, net 优先级, 连接要求

#### 技术实现
- **格式**: NetworkX 图或 PyTorch Geometric 数据结构
- **编码器**: GNN (GraphSAGE, GCN) 或图 Transformer
- **特征**: 节点坐标, 连接权重, 类型编码

#### 优势
- 精确表达电气连接关系
- 支持图论算法优化
- 天然匹配 PCB 的拓扑结构

#### 适用任务
- NetRegionMatch: 图匹配和路径规划
- MockPatchPrediction: 连接关系引导的动作

## 模态组合策略

### 基础组合 (v1 重点验证)

#### 组合 A: 几何 + 图像
- **输入**: geometry_grid + board_image
- **适用**: 空间感知 + 视觉理解
- **优势**: 平衡结构化和视觉信息

#### 组合 B: 几何 + 文本
- **输入**: geometry_grid + text_rules
- **适用**: 空间约束 + 规则推理
- **优势**: 精确表达设计规范

#### 组合 C: 图像 + 图结构
- **输入**: board_image + graph_structure
- **适用**: 视觉布局 + 连接关系
- **优势**: 直观布局 + 电气逻辑

#### 组合 D: 全模态融合
- **输入**: geometry_grid + board_image + text_rules + graph_structure
- **适用**: 完整信息整合
- **挑战**: 特征对齐和计算复杂度

### 验证计划

#### Phase 1: 单模态基准
- 分别测试每个模态的独立效果
- 建立性能基线和计算开销基准

#### Phase 2: 双模态组合
- 测试基础组合 A/B/C
- 比较融合策略（concat, cross-attention, etc.）

#### Phase 3: 多模态扩展
- 测试全模态融合
- 评估增益是否值得复杂度提升

## 模型后端适配

### Tiny Baseline
- **几何**: CNN encoder
- **图像**: ResNet/ViT
- **文本**: 跳过或简单 embedding
- **图**: MLP 或跳过

### DeepSeek-VL
- **几何**: 转换为图像或跳过
- **图像**: 原生支持
- **文本**: 原生支持
- **图**: 需要转换为文本描述

### Janus
- **几何**: 转换为图像
- **图像**: 原生支持
- **文本**: 原生支持
- **图**: 需要转换为文本或图像描述

## 评估指标

### 模态效果指标
- **任务准确率**: 分类/排序/匹配任务的性能
- **收敛速度**: 达到相同性能所需训练步数
- **计算效率**: GPU 内存使用和推理时间
- **泛化能力**: 在不同 PCB 复杂度上的表现

### 组合优势指标
- **增益比**: 多模态 vs 单模态性能提升
- **互补性**: 不同模态间的相关性和冗余度
- **鲁棒性**: 对噪声和缺失模态的抵抗力

## 实现优先级

1. **Phase 1**: 几何栅格和图像模态 (最直接相关)
2. **Phase 2**: 添加文本规则 (增强约束表达)
3. **Phase 3**: 集成图结构 (完整拓扑信息)

## 注意事项

- 模态对齐：不同模态的时空分辨率需要协调
- 数据同步：确保所有模态来自同一 PCB 状态
- 计算平衡：在性能和复杂度间取舍
- 可解释性：保持模态贡献的可追踪性