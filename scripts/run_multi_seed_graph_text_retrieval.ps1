# GraphTextRetrieval 多 seed 复现脚本（Stage 1 Adapter 基线）
# 用途：用 3 个不同 seed 训练并评估，判断 adapter 基线是否稳定
# 前置：已构建 data/embedding/graph_text_pairs（或运行 build-pairs）
# OOD：test split 为 board-disjoint，即为 OOD

param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Config = ".\configs\training\embedding_qwen3_0_6b.yaml",
    [string]$BaseOutput = ".\outputs\qwen3_embedding_graph_text",
    [int[]]$Seeds = @(7, 42, 123)
)

$ErrorActionPreference = "Stop"

Write-Host "=== GraphTextRetrieval 多 seed 训练与评估 (Stage 1 Adapter) ==="
Write-Host ""

$results = @()

foreach ($seed in $Seeds) {
    $outDir = "${BaseOutput}_seed${seed}"
    Write-Host "--- seed $seed ---"
    & $PythonExe .\apps\embedding_train_cli.py --config $Config --output-dir $outDir --seed $seed
    if ($LASTEXITCODE -ne 0) { throw "Train seed=$seed failed" }

    $ckpt = Join-Path $outDir "checkpoints\best_model.pt"

    Write-Host "  Eval test (OOD)..."
    $evalTest = & $PythonExe .\apps\embedding_eval_cli.py --config $Config --checkpoint $ckpt --split test 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Eval test seed=$seed failed" }
    $evalTest | Out-File -FilePath ".\outputs\embedding_eval_seed${seed}_test.json" -Encoding utf8

    Write-Host "  Eval test noise_std=0.05..."
    $evalNoise = & $PythonExe .\apps\embedding_eval_cli.py --config $Config --checkpoint $ckpt --split test --noise-std 0.05 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Eval noise seed=$seed failed" }
    $evalNoise | Out-File -FilePath ".\outputs\embedding_eval_seed${seed}_noise005.json" -Encoding utf8

    $results += [pscustomobject]@{ Seed = $seed; Test = $evalTest; Noise005 = $evalNoise }
}

Write-Host ""
Write-Host "=== 合并报告 ==="
& $PythonExe .\scripts\merge_multi_seed_embedding_report.py --output .\outputs\embedding_multi_seed_report.json
if ($LASTEXITCODE -ne 0) { Write-Warning "Merge failed (non-fatal)" }

Write-Host ""
Write-Host "完成。报告: outputs/embedding_multi_seed_report.json"
Write-Host "各 seed 输出: ${BaseOutput}_seed*"
