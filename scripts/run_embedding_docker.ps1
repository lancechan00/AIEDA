param(
    [string]$ComposeFile = ".\docker\compose.embedding.yml"
)

Write-Host "Build embedding image"
docker compose -f $ComposeFile build

Write-Host "Run formal training in docker"
docker compose -f $ComposeFile run --rm embedding-train

Write-Host "Run evaluation in docker"
docker compose -f $ComposeFile run --rm embedding-train python apps/embedding_eval_cli.py --config configs/training/embedding_qwen3_0_6b.yaml --checkpoint outputs/qwen3_embedding_graph_text/checkpoints/best_model.pt --split test
