# 隐私与路径审计报告（开源准备）

本文档记录工程中可能暴露个人电脑信息的路径、用户名等，以及对应的 env 化 / 相对路径改造方案。

## 1. 扫描结果汇总

### 1.1 涉及个人路径的文件

| 类型 | 路径/文件 | 问题 | 建议 |
|------|------------|------|------|
| **生成数据** | `data/embedding/parsed/*.json` | `metadata.source_files.pcb`、`metadata.parsed_at` 含本地绝对路径 | 代码改为写入相对路径 |
| **生成数据** | `data/embedding/raw_manifest.json` | `source_dir`、`projects[].project_dir`、`pcb_files` 等含绝对路径 | 同上 |
| **生成数据** | `data/embedding/raw/download_summary.json` | `manifest`、`output_dir`、`downloaded_project_dirs` 含绝对路径 | 同上 |
| **生成数据** | `outputs/*/training_summary.json` | `output_dir` 含绝对路径 | 同上 |
| **上游数据** | `data/embedding/raw/**/*.kicad_pcb` | 部分含 KiCad 3D 模型路径（工程自带） | 不修改；`data/embedding/raw/` 已加入 .gitignore |

### 1.2 代码中写入绝对路径的位置

| 模块 | 文件 | 行号 | 问题 | 改造 |
|------|------|------|------|------|
| 解析器 | `packages/data_pipeline/parsers/kicad_parser.py` | 107-111 | `pcb`、`parsed_at` 用 `str(Path)` 可能为绝对路径 | 改为相对路径 |
| 审计 | `packages/data_pipeline/loaders/source_auditor.py` | 19-76 | `source_dir`、`project_dir`、`pcb_files` 等用 `.resolve()` | 改为相对路径 |
| 下载 | `scripts/github_kicad_download.py` | 161-163, 155 | `manifest`、`output_dir`、`downloaded_project_dirs` 用 `.resolve()` | 改为相对路径 |
| 训练 | `packages/training/trainers/embedding_trainer.py` | 170 | `output_dir` 写入 training_summary | 改为相对路径 |
| 训练 | `packages/training/trainers/trainer.py` | 110 | 同上 | 同上 |

### 1.3 敏感配置（已处理）

| 项目 | 状态 |
|------|------|
| `.env` | 已在 .gitignore，含 `GITHUB_TOKEN` |
| `GITHUB_TOKEN` | 脚本从 `os.getenv("GITHUB_TOKEN")` 读取，无硬编码 |
| `secrets/` | 已在 .gitignore |

---

## 2. 环境变量方案

### 2.1 新增 / 使用环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `AIEDA_ROOT` | 项目根目录，用于将路径转为相对路径 | 当前工作目录或 `__file__` 推导 |
| `GITHUB_TOKEN` | GitHub API 调用（已在使用） | 无，可选 |
| `HF_TOKEN` | HuggingFace 模型拉取（如需要） | 无，可选 |

### 2.2 .env.example

```bash
# GitHub API token（可选，用于提升 discovery 额度）
# GITHUB_TOKEN=ghp_xxx

# 项目根目录（可选，用于路径可移植性）
# AIEDA_ROOT=/path/to/AIEDA
```

---

## 3. 改造原则

1. **写入 JSON 的路径**：优先使用**相对于项目根**或**相对于数据根**的相对路径。
2. **读取路径**：支持相对路径；若为相对路径，则相对于当前工作目录或 `AIEDA_ROOT` 解析。
3. **生成数据**：`data/embedding/raw/`、`data/embedding/parsed/`、`outputs/` 等建议加入 .gitignore，或仅提交不含个人路径的示例数据。

---

## 4. .gitignore 已补充

当前已忽略：

- `data/raw/`、`data/processed/`、`outputs/`
- `data/embedding/raw/`、`data/embedding/parsed/`、`data/embedding/graph_text_pairs/`
- `data/embedding/raw_manifest.json`

`download_summary.json` 位于 `data/embedding/raw/` 内，已随目录忽略。

---

## 5. 已实施改造（代码）

- [x] `kicad_parser.py`：`pcb`、`parsed_at` 改为相对路径
- [x] `source_auditor.py`：`source_dir`、`project_dir`、`pcb_files` 等改为相对路径
- [x] `github_kicad_download.py`：`manifest`、`output_dir`、`downloaded_project_dirs` 改为相对路径
- [x] `embedding_trainer.py` / `trainer.py`：`output_dir` 在 summary 中存为相对路径
- [x] 新增 `.env.example`
- [x] 更新 `.gitignore` 与 README
