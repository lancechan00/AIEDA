param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$RawDir = ".\data\embedding\raw",
    [string]$ParsedDir = ".\data\embedding\parsed",
    [string]$PairDir = ".\data\embedding\graph_text_pairs",
    [string]$Config = ".\configs\training\embedding_qwen3_0_6b.yaml"
)

Write-Host "1) Audit raw KiCad sources"
& $PythonExe .\apps\data_cli.py audit-sources --source-dir $RawDir --output-file .\data\embedding\raw_manifest.json

Write-Host "2) Parse KiCad projects"
& $PythonExe .\apps\data_cli.py parse --source-dir $RawDir --output-dir $ParsedDir --parallel 4

Write-Host "3) Build graph-text pairs"
& $PythonExe .\apps\data_cli.py build-pairs --parsed-dir $ParsedDir --output-dir $PairDir --seed 7 --negatives-per-sample 2

Write-Host "4) Train embedding model (local debug)"
& $PythonExe .\apps\embedding_train_cli.py --config $Config

Write-Host "5) Evaluate on test split"
& $PythonExe .\apps\embedding_eval_cli.py --config $Config --checkpoint .\outputs\qwen3_embedding_graph_text\checkpoints\best_model.pt --split test
