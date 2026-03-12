# LocalRouteChoice-Lite 板级扩数脚本
# 用途：在已更新白名单后，拉取、解析、构建数据集，并记录扩数前后统计
# 前置：可先手动往 data/embedding/github_whitelist.json 添加新仓库（参考 data_expansion_guide_v1.md 5.2）

param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Whitelist = ".\data\embedding\github_whitelist.json",
    [string]$RawDir = ".\data\embedding\raw",
    [string]$ParsedDir = ".\data\embedding\parsed",
    [string]$OutputDir = ".\data\local_route_choice_lite_github",
    [int]$DownloadLimit = 50
)

$ErrorActionPreference = "Stop"

Write-Host "=== 1. 下载（使用当前白名单）==="
if (-not (Test-Path $Whitelist)) {
    Write-Error "Whitelist not found: $Whitelist. Run github_kicad_discovery first or create manually."
}
& $PythonExe .\scripts\github_kicad_download.py --manifest $Whitelist --output-dir $RawDir --limit $DownloadLimit
if ($LASTEXITCODE -ne 0) { throw "Download failed" }

Write-Host ""
Write-Host "=== 2. 解析 KiCad 工程 ==="
& $PythonExe .\apps\data_cli.py parse --source-dir $RawDir --output-dir $ParsedDir --parallel 4
if ($LASTEXITCODE -ne 0) { throw "Parse failed" }

Write-Host ""
Write-Host "=== 3. 构建 LocalRouteChoice-Lite ==="
& $PythonExe .\apps\data_cli.py build --parsed-dir $ParsedDir --output-dir $OutputDir
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

Write-Host ""
Write-Host "=== 4. 审计类别分布 ==="
& $PythonExe .\scripts\audit_local_route_choice_dataset.py --data-dir $OutputDir --output .\outputs\audit_after_expansion.json
if ($LASTEXITCODE -ne 0) { Write-Warning "Audit failed (non-fatal)" }

Write-Host ""
Write-Host "完成。数据集: $OutputDir"
Write-Host "请查看 dataset_summary.json 和 outputs/audit_after_expansion.json"
Write-Host "下一轮训练: .\scripts\run_multi_seed_local_route_choice.ps1"
Write-Host ""
Write-Host "扩数收益跟踪：将本轮 board 数、样本数记录到 docs/training/expansion_log.md"
