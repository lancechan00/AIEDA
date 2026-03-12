# LocalRouteChoice-Lite 数据扩充脚本
# 前置条件：已运行 run_kicad_github_pipeline.ps1 完成 discovery/download/parse，或 parsed 目录已有数据
# 用途：从 data/embedding/parsed 构建/重建 LocalRouteChoice-Lite 数据集

param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$ParsedDir = ".\data\embedding\parsed",
    [string]$OutputDir = ".\data\local_route_choice_lite_github"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ParsedDir)) {
    Write-Error "Parsed dir not found: $ParsedDir. Run run_kicad_github_pipeline.ps1 first."
}

Write-Host "Building LocalRouteChoice-Lite from parsed boards..."
& $PythonExe .\apps\data_cli.py build --parsed-dir $ParsedDir --output-dir $OutputDir

if ($LASTEXITCODE -ne 0) {
    throw "LocalRouteChoice build failed, exit code=$LASTEXITCODE"
}

Write-Host "Done. Dataset: $OutputDir"
Write-Host "Check dataset_summary.json for split and label stats."
