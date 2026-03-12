#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
CONFIG_PATH="${CONFIG_PATH:-configs/training/embedding_qwen3_0_6b.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/qwen3_embedding_remote}"

echo "Start remote training"
"${PYTHON_BIN}" apps/embedding_train_cli.py --config "${CONFIG_PATH}" --output-dir "${OUTPUT_DIR}"

echo "Evaluate remote checkpoint on test split"
"${PYTHON_BIN}" apps/embedding_eval_cli.py \
  --config "${CONFIG_PATH}" \
  --checkpoint "${OUTPUT_DIR}/checkpoints/best_model.pt" \
  --split test

echo "Evaluate robustness with noisy graph features"
"${PYTHON_BIN}" apps/embedding_eval_cli.py \
  --config "${CONFIG_PATH}" \
  --checkpoint "${OUTPUT_DIR}/checkpoints/best_model.pt" \
  --split test \
  --noise-std 0.05
