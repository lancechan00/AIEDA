# Qwen3-Embedding-0.6B 训练 Runbook（v1）

## 1. 数据准备

### 1.0 GitHub 白名单采集（推荐）

```powershell
python .\scripts\github_kicad_discovery.py --output-file .\data\embedding\github_whitelist.json --target-count 30 --max-pages 3 --per-page 20
python .\scripts\github_kicad_download.py --manifest .\data\embedding\github_whitelist.json --output-dir .\data\embedding\raw --limit 30
```

或一键执行：

```powershell
.\scripts\run_kicad_github_pipeline.ps1
```

### 1.1 审计原始数据

```powershell
python .\apps\data_cli.py audit-sources --source-dir .\data\embedding\raw --output-file .\data\embedding\raw_manifest.json
```

### 1.2 解析 KiCad 工程

```powershell
python .\apps\data_cli.py parse --source-dir .\data\embedding\raw --output-dir .\data\embedding\parsed --parallel 4
```

### 1.3 构建 graph-text pairs

```powershell
python .\apps\data_cli.py build-pairs --parsed-dir .\data\embedding\parsed --output-dir .\data\embedding\graph_text_pairs --seed 7 --negatives-per-sample 2
```

## 2. 本地 GPU 调试（小样本）

目标：先验证链路可跑，不追求最终效果。

### 2.1 配置建议（A4000 16G）

- 固定 `text_encoder_mode: qwen`
- `freeze_text_encoder: true`
- `epochs`: 1（先 smoke），正式可调到 3-8
- `batch_size`: 2 或 4 起步（A4000 通常可升到 8，视文本长度）
- `max_text_length`: 256（显存紧张时可降到 192/128）

### 2.2 训练

```powershell
python .\apps\embedding_train_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml
```

### 2.3 评估

```powershell
python .\apps\embedding_eval_cli.py --config .\configs\training\embedding_qwen3_0_6b.yaml --checkpoint .\outputs\qwen3_embedding_graph_text\checkpoints\best_model.pt --split test
```

## 3. 远端正式训练（大样本）

推荐步骤：

1. 本地打包 `data/embedding/graph_text_pairs`。
2. 上传到远端，保持同目录结构。
3. 保持 `text_encoder_mode: qwen`，并确认可拉取模型权重。
4. 运行正式训练，增加 `epochs` 和 `batch_size`。

远端命令示例：

```bash
python apps/embedding_train_cli.py --config configs/training/embedding_qwen3_0_6b.yaml --output-dir outputs/qwen3_embedding_remote
python apps/embedding_eval_cli.py --config configs/training/embedding_qwen3_0_6b.yaml --checkpoint outputs/qwen3_embedding_remote/checkpoints/best_model.pt --split test
```

## 3.1 Docker 正式训练（Win11 + A4000）

```powershell
.\scripts\run_embedding_docker.ps1
```

等价命令：

```powershell
docker compose -f .\docker\compose.embedding.yml build
docker compose -f .\docker\compose.embedding.yml run --rm embedding-train
docker compose -f .\docker\compose.embedding.yml run --rm embedding-train python apps/embedding_eval_cli.py --config configs/training/embedding_qwen3_0_6b.yaml --checkpoint outputs/qwen3_embedding_graph_text/checkpoints/best_model.pt --split test
```

## 4. 验收指标

至少观察以下指标：

- `recall_at_1`
- `recall_at_3`
- `recall_at_5`
- `mrr`
- `avg_pos_neg_gap`

增强评估：

- 噪声敏感性：`--noise-std 0.05`
- OOD split（可选）：单独构建 `test_ood` 并评估

## 5. 常见问题

### Qwen 权重无法拉取

先确认网络和 HuggingFace 访问，再执行：

```powershell
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen3-Embedding-0.6B', trust_remote_code=True); print('ok')"
```

如果短期无法拉取，可临时改为 `hash` 做流程调试，但正式实验仍应回到固定 `qwen`。

### 显存不足

- 降低 `batch_size`
- 降低 `max_text_length`
- 先冻结文本塔（默认已开启）
