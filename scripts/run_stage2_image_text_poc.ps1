# Stage 2 Image-Text Retrieval PoC
# 用途：用 Qwen3-VL-Embedding-2B 对 PCB 渲染图做 image-text 检索
# 前置：已构建 data/embedding/image_text_pairs
# 依赖：pip install ai-eda[stage2]

param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$DataDir = ".\data\embedding\image_text_pairs",
    [string]$Split = "test",
    [string]$Output = ".\outputs\stage2_image_text_poc.json"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Stage 2 Image-Text PoC (Qwen3-VL-Embedding-2B) ==="
Write-Host ""

if (-not (Test-Path "$DataDir\$Split\data.jsonl")) {
    Write-Host "请先构建 image-text pairs:"
    Write-Host "  python .\apps\data_cli.py build-image-pairs --parsed-dir .\data\embedding\parsed --output-dir $DataDir"
    exit 1
}

& $PythonExe .\apps\image_text_retrieval_poc.py --data-dir $DataDir --split $Split --output $Output --batch-size 2
if ($LASTEXITCODE -ne 0) { throw "PoC failed" }

Write-Host ""
Write-Host "完成。报告: $Output"
