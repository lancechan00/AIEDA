# LocalRouteChoice-Lite 多 seed 复现脚本
# 用途：用 3 个不同 seed 训练并评估，判断 68.8% 是否稳定
# 前置：已构建 data/local_route_choice_lite_github

param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Config = ".\configs\training\task_v1_github.yaml",
    [string]$BaseOutput = ".\outputs\tiny_baseline_github",
    [int[]]$Seeds = @(7, 42, 123)
)

$ErrorActionPreference = "Stop"

Write-Host "=== 1. 审计类别分布 ==="
& $PythonExe .\scripts\audit_local_route_choice_dataset.py --data-dir .\data\local_route_choice_lite_github --output .\outputs\multi_seed_audit.json
if ($LASTEXITCODE -ne 0) { throw "Audit failed" }

Write-Host ""
Write-Host "=== 2. 多 seed 训练与评估 ==="
$results = @()

foreach ($seed in $Seeds) {
    $outDir = "${BaseOutput}_seed${seed}"
    Write-Host "--- seed $seed ---"
    & $PythonExe .\apps\train_cli.py --config $Config --output-dir $outDir --seed $seed
    if ($LASTEXITCODE -ne 0) { throw "Train seed=$seed failed" }

    $ckpt = Join-Path $outDir "checkpoints\best_model.pt"
    Write-Host "Evaluating $ckpt"
    $evalOut = & $PythonExe .\apps\eval_cli.py --config $Config --checkpoint $ckpt --split test
    if ($LASTEXITCODE -ne 0) { throw "Eval seed=$seed failed" }
    $evalOut | Out-File -FilePath ".\outputs\eval_seed${seed}.json" -Encoding utf8
    $results += [pscustomobject]@{ Seed = $seed; Output = $evalOut }
}

Write-Host ""
Write-Host "=== 3. 汇总 ==="
foreach ($r in $results) {
    Write-Host "seed $($r.Seed): $($r.Output)"
}

Write-Host ""
Write-Host "=== 4. 合并报告 ==="
& $PythonExe .\scripts\merge_multi_seed_report.py --audit .\outputs\multi_seed_audit.json --evals .\outputs\eval_seed*.json --output .\outputs\multi_seed_audit.json
if ($LASTEXITCODE -ne 0) { Write-Warning "Merge failed (non-fatal)" }

Write-Host ""
Write-Host "完成。完整报告: outputs/multi_seed_audit.json"
Write-Host "各 seed 输出: ${BaseOutput}_seed*"
