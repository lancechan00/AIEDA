# 脱敏路径下的完整流程（开源可复现）

本文档说明在**无本地绝对路径**的前提下，从零完成爬虫 → 训练 → 评估的全流程。所有生成数据均使用相对路径，可在任意机器上复现。

## 前置条件

- Python 3.8+
- 项目根目录执行（`cd` 到 AIEDA 根目录）
- 可选：`.env` 中配置 `GITHUB_TOKEN` 提升 discovery API 额度

## 1. 爬虫 + 数据准备（全流程）

```powershell
# 一键执行：discovery → download → audit → parse → build-pairs
.\scripts\run_kicad_github_pipeline.ps1
```

或分步执行：

```powershell
# Step 1: 发现 GitHub KiCad 仓库
.\.venv\Scripts\python.exe .\scripts\github_kicad_discovery.py --output-file .\data\embedding\github_whitelist.json --target-count 30 --max-pages 3 --per-page 20

# Step 2: 下载到 raw
.\.venv\Scripts\python.exe .\scripts\github_kicad_download.py --manifest .\data\embedding\github_whitelist.json --output-dir .\data\embedding\raw --limit 30

# Step 3: 审计 raw 源
.\.venv\Scripts\python.exe .\apps\data_cli.py audit-sources --source-dir .\data\embedding\raw --output-file .\data\embedding\raw_manifest.json

# Step 4: 解析 KiCad 工程
.\.venv\Scripts\python.exe .\apps\data_cli.py parse --source-dir .\data\embedding\raw --output-dir .\data\embedding\parsed --parallel 4

# Step 5: 构建 graph-text pairs
.\.venv\Scripts\python.exe .\apps\data_cli.py build-pairs --parsed-dir .\data\embedding\parsed --output-dir .\data\embedding\graph_text_pairs --seed 7 --negatives-per-sample 2
```

**脱敏说明**：上述命令全部使用相对路径（`.\data\embedding\...`），生成的 JSON 中路径均为相对路径，不含 `D:\`、`C:\Users\` 等。

## 2. 训练

```powershell
# 使用默认配置（相对路径）
.\.venv\Scripts\python.exe .\apps\embedding_train_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml
```

或 A4000 调试配置：

```powershell
.\.venv\Scripts\python.exe .\apps\embedding_train_cli.py --config .\configs\training\embedding_qwen3_0_6b_a4000_debug.yaml
```

## 3. 评估

```powershell
.\.venv\Scripts\python.exe .\apps\embedding_eval_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml --checkpoint .\outputs\qwen3_embedding_graph_text\checkpoints\best_model.pt --split test
```

## 4. .gitignore 与不提交内容

以下目录/文件由 pipeline 生成，含相对路径或 API 结果，已加入 `.gitignore`，**不应提交**：

- `data/embedding/raw/`
- `data/embedding/parsed/`
- `data/embedding/graph_text_pairs/`
- `data/embedding/raw_manifest.json`
- `data/embedding/github_whitelist.json`
- `outputs/`

克隆后需自行运行 pipeline 生成数据。

## 5. 若已有旧数据（含绝对路径）

若 `data/embedding/parsed/` 中 JSON 仍含 `D:\`、`C:\Users\` 等路径，需重新执行 Step 4 和 Step 5：

```powershell
.\.venv\Scripts\python.exe .\apps\data_cli.py parse --source-dir .\data\embedding\raw --output-dir .\data\embedding\parsed --parallel 4
.\.venv\Scripts\python.exe .\apps\data_cli.py build-pairs --parsed-dir .\data\embedding\parsed --output-dir .\data\embedding\graph_text_pairs --seed 7 --negatives-per-sample 2
```
