### 研发目录结构推荐

基于你的框架图（我已从描述中理解：上半部分是一个复杂流程，包括输入处理、扩散模型生成、几何/图编码、PCB线路输出、Checker/Router/DRC验证，以及Playwright可视化；下半部分是简化版，聚焦Policy/Planner、Diff/Patch、State/Router/DRC、Observation编码），我推荐一个标准的Python/ML项目目录结构。这结构适合你的需求：存放整体设计文档（从第一版框架开始）、模块化开发（每个模块涉及训练、服务接口）、运行/测试集成。它模块化，便于扩展到多模态模型、开源数据库使用，并支持版本控制（e.g., Git）。

心智模型：想想这像一个“工厂布局”——docs是蓝图仓库，src是生产线（模块代码），data是原材料，experiments是测试车间，services是组装线。优先存放你的第一版框架文档在docs/designs/v1.md 或类似。

#### 推荐目录结构
```
pcb-auto-routing-project/  # 项目根目录
├── README.md              # 项目概述、安装指南、运行示例
├── requirements.txt       # Python依赖（如torch, transformers, networkx）
├── setup.py               # 如果打包成包（可选）
├── .gitignore             # 忽略data/large_files等
├── docs/                  # 存放整体设计文档、框架图、报告
│   ├── designs/           # 设计文档
│   │   ├── v1_framework.md  # 你当前的第一版框架描述（包括上传的图解释）
│   │   ├── v2_enhanced.md   # 未来迭代版本
│   │   └── modules_breakthrough.md  # 你要的重点突破模块文档（下面我会提供内容草稿）
│   ├── api/               # 服务接口文档（e.g., FastAPI endpoints）
│   └── reports/           # 深度报告、实验结果（e.g., MCP版本建议）
├── src/                   # 核心源代码
│   ├── __init__.py
│   ├── main.py            # 入口脚本：汇总连接模块、运行整个系统（e.g., load model -> process input -> route -> check DRC）
│   ├── modules/           # 每个框架模块的代码（对应你的图：训练、接口独立）
│   │   ├── state_encoder/ # 状态编码器（geometry/graph）
│   │   │   ├── __init__.py
│   │   │   ├── encoder.py # 核心编码逻辑（e.g., GNN for graph, CNN for geometry）
│   │   │   ├── train.py   # 训练脚本
│   │   │   └── api.py     # 服务接口（e.g., Flask/REST endpoint for encoding）
│   │   ├── policy_planner/# Policy/Planner模块（决策层）
│   │   │   ├── __init__.py
│   │   │   ├── planner.py # 核心逻辑（e.g., 多模态Transformer）
│   │   │   ├── train.py
│   │   │   └── api.py
│   │   ├── diff_patch/    # Diff/Patch模块（扩散模型辅助）
│   │   │   ├── __init__.py
│   │   │   ├── patcher.py # 生成diff/patch
│   │   │   ├── train.py
│   │   │   └── api.py
│   │   ├── router/        # Router模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py  # 路径规划（e.g., A* with AI guidance）
│   │   │   └── api.py     # 接口（无train，除非RL增强）
│   │   ├── checker_drc/   # Checker/Router/DRC模块（验证层）
│   │   │   ├── __init__.py
│   │   │   ├── checker.py # DRC检查逻辑
│   │   │   └── api.py     # 接口（集成EDA如KiCad API）
│   │   └── utils/         # 共享工具（e.g., input_output.py for 数据处理）
│   ├── pipelines/         # 汇总运行脚本（连接模块）
│   │   ├── train_pipeline.py  # 全系统训练（e.g., finetune多模态 + train encoders）
│   │   └── inference_pipeline.py  # 推理运行（输入netlist/layout -> 输出routing）
│   └── visualization/     # 可视化模块（e.g., Playwright/ Matplotlib for PCB图）
│       ├── __init__.py
│       └── viz.py         # 生成框架图/PCB渲染
├── data/                  # 开源数据库/数据集
│   ├── raw/               # 原始数据（e.g., 下载的KiCad PCB文件、netlist）
│   ├── processed/         # 处理后数据（e.g., encoded geometry/graph）
│   ├── models/            # 训练好的模型权重（e.g., finetuned DeepSeek）
│   └── datasets/          # 脚本下载/准备数据（e.g., from GitHub PCB repos）
├── experiments/           # 测试任务/实验
│   ├── notebooks/         # Jupyter notebooks for 原型测试（e.g., test_state_encoder.ipynb）
│   ├── logs/              # 训练日志（TensorBoard兼容）
│   ├── results/           # 测试结果（e.g., DRC pass率、线长指标）
│   └── configs/           # YAML配置（e.g., train_config.yaml for hyperparameters）
├── tests/                 # 单元/集成测试
│   ├── __init__.py
│   ├── test_modules.py    # 测试每个模块（e.g., pytest for encoder）
│   └── test_pipeline.py   # 全系统测试（e.g., sample PCB输入）
├── services/              # 服务接口（如果部署为API）
│   ├── __init__.py
│   ├── app.py             # FastAPI/Flask主服务（汇总模块API）
│   └── docker-compose.yml # 部署配置（可选，容器化）
└── scripts/               # 辅助脚本（e.g., download_data.sh, visualize_framework.py）
```

- **为什么这样设计？**
  - **文档优先**：docs/存放你的v1框架（直接复制图描述到md，用Mermaid语法重绘图）。每个模块有独立子目录，便于“模型训练、服务接口”分离（e.g., train.py vs api.py）。
  - **模块化**：对应你的框架，每个关键模块（state_encoder等）自成一体，便于独立开发/测试。
  - **运行/测试集成**：pipelines/连接一切（e.g., main.py调用所有模块）。experiments/用于迭代测试任务（如简单板vs复杂板）。
  - **可扩展**：data/支持开源数据库（下面文档详述）。用Git submodules管理开源模型（如DeepSeek仓库）。
  - **工具链**：用Poetry/Pipenv管理依赖；Pytest for tests；Black/Flake8 for代码风格。

起步：先创建docs/designs/v1_framework.md，粘贴你的图描述。然后在src/main.py写一个dummy运行流程。

### 重点突破模块的文档

以下是`docs/modules_breakthrough.md`的内容草稿。这份文档聚焦你的需求：基于开源多模态模型（如DeepSeek）、开源数据库、训练核心思路、输入输出处理。同时解释每个模块（checker、router、DRC、状态编码器）的意义、技术规范、MCP（Minimum Viable Product）版本建议（首版简单，深度报告式分析）。我用Markdown结构化，便于阅读/扩展。

#### 1. 总体训练核心思路（基于开源多模态模型）
- **开源多模态模型选择**：首推DeepSeek-Janus（开源，Hugging Face可用，4.5B参数，支持文本+图像融合）。备选：LLaMA-3 with MMProjector（Meta开源）。为什么？易finetune，低成本添加自定义模态（如电路图GNN）。
- **开源数据库**：用KiCad/Altium开源项目（GitHub搜索"PCB dataset"，e.g., PCBNet数据集~1k样本）；补充Google Dataset Search的"PCB routing data"；合成数据用Python脚本生成随机netlist/layout（用NetworkX模拟图）。
- **训练思路**：分层finetune。
  - **阶段1**：预处理数据（netlist->graph, layout->geometry image/grid）。
  - **阶段2**：用LoRA finetune DeepSeek on你的模态（电路embedding）。监督信号：预测正确routing路径（loss=路径相似度+DRC分数）。
  - **阶段3**：RL增强（PPO算法，奖励=完成率-线长-via数）。数据规模：起步1k样本，迭代到10k。
  - **输入处理**：Netlist (JSON/graph) + Layout (image/grid) + Rules (text) -> 多模态embedding（用cross-attention融合）。
  - **输出处理**：结构化DSL (e.g., YAML路径序列) -> 转EDA格式（用KiCad Python API渲染/检查）。
- **深度报告建议**：首版MCP：用小数据集（100样本）finetune，测简单双层板。指标：DRC pass>80%。挑战：注意力分散->用RL校准。未来：加扩散辅助（Stable Diffusion finetune on PCB热图）。

#### 2. 状态编码器（Geometry/Graph）
- **存在意义**：你的框架核心（observation->决策）。它“记住”板子状态：几何（空间堵塞/通道）+图（net连接）。像“棋盘扫描仪”，提供多模态输入给planner，避免模型只看局部。
- **可选择技术规范**：Geometry：CNN (ResNet) or Vision Transformer (ViT)编码图像/grid。Graph：GNN (GraphSAGE/PyG库)编码netlist。融合：Concat + Linear层。
- **MCP版本建议**（首版简单）**：用PyG GNN for graph + Simple CNN for geometry。输入：Netlist (nodes=pins, edges=connections) + Grid (2D array of obstacles)。输出：Fixed-size embedding (512 dim)。训练：独立监督（predict拥塞热图）。深度报告：复杂度O(N^2) for graphs，MCP测试简单板（<100 nets），成功率>90%编码准确。

#### 3. Checker/Router/DRC（验证/路由层）
- **Checker存在意义**：后置验证生成的routing，确保“工程合法”（e.g., 无短路、间距OK）。像“质检员”，补模型hallucination。
- **Router存在意义**：执行规划路径（A* or rip-up-reroute），用AI建议（如planner的waypoint）指导。像“工人”，结合传统算法+AI全局感。
- **DRC存在意义**：专查设计规则（线宽、via规则）。集成EDA，避免纯AI输出无效。
- **可选择技术规范**：Checker：Python规则引擎（e.g., Shapely for几何检查）。Router：FreeRouting库（开源Java/Python wrapper）or NetworkX路径算法。DRC：KiCad DRC API（Python绑定）or自定义规则检查器（用SciPy距离计算）。
- **MCP版本建议**（首版简单）**：Checker用Shapely check交集/short。Router用A* (scipy.sparse.csgraph)。DRC用简单规则列表（if-else）。输入：路径序列。输出：Pass/Fail + 修正建议。深度报告：传统router弱全局->AI提升20%完成率。MCP：双层板测试，集成时间<1周。

#### 4. 其它模块（Policy/Planner, Diff/Patch）
- **Policy/Planner**：决策层。意义：像“棋手”，用多模态输出动作序列。规范：Transformer decoder。MCP：Finetune DeepSeek，autoregressive生成路径。
- **Diff/Patch**：辅助生成“补丁”（e.g., 扩散热图修局部）。意义：提供大局观。规范：Conditional Diffusion (Diffusers库)。MCP：简单U-Net生成拥塞图。

#### 5. 系统整体提示
- **集成**：用pipelines/train_pipeline.py连接（e.g., encoder -> planner -> router -> drc）。
- **测试任务**：experiments/下建notebook：输入sample netlist，输出routing，测指标。
- **风险/迭代**：数据稀缺->合成更多。计算：消费GPU finetune。

这份文档可直接复制到你的项目。下一步，如果你提供具体代码需求，我可以帮草拟src/modules/state_encoder/encoder.py！