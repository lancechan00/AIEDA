param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Whitelist = ".\data\embedding\github_whitelist.json",
    [string]$RawDir = ".\data\embedding\raw",
    [string]$ParsedDir = ".\data\embedding\parsed",
    [string]$PairsDir = ".\data\embedding\graph_text_pairs",
    [int]$TargetCount = 30,
    [int]$Limit = 30
)

$ErrorActionPreference = "Stop"

function Run-Step {
    param(
        [string]$Label,
        [scriptblock]$Action
    )
    Write-Host $Label
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed ($Label), exit code=$LASTEXITCODE"
    }
}

Run-Step "Step 1: Discover GitHub KiCad repositories" {
    & $PythonExe .\scripts\github_kicad_discovery.py --output-file $Whitelist --target-count $TargetCount --max-pages 3 --per-page 20
}

Run-Step "Step 2: Download repositories to raw data dir" {
    & $PythonExe .\scripts\github_kicad_download.py --manifest $Whitelist --output-dir $RawDir --limit $Limit
}

Run-Step "Step 3: Audit raw KiCad sources" {
    & $PythonExe .\apps\data_cli.py audit-sources --source-dir $RawDir --output-file .\data\embedding\raw_manifest.json
}

Run-Step "Step 4: Parse KiCad projects" {
    & $PythonExe .\apps\data_cli.py parse --source-dir $RawDir --output-dir $ParsedDir --parallel 4
}

Run-Step "Step 5: Build graph-text pairs" {
    & $PythonExe .\apps\data_cli.py build-pairs --parsed-dir $ParsedDir --output-dir $PairsDir --seed 7 --negatives-per-sample 2
}
