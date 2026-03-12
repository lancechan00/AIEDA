param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [string]$Config = ".\configs\training\embedding_qwen3_0_6b_a4000_debug.yaml"
)

Write-Host "Check CUDA visibility"
& $PythonExe -c "import torch; print('cuda_available=', torch.cuda.is_available()); print('device_count=', torch.cuda.device_count())"

Write-Host "Check HuggingFace access for Qwen3-Embedding-0.6B"
& $PythonExe -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen3-Embedding-0.6B', trust_remote_code=True); print('hf_ok=True')"

Write-Host "Run A4000 debug training"
& $PythonExe .\apps\embedding_train_cli.py --config $Config

Write-Host "Run A4000 debug evaluation"
& $PythonExe .\apps\embedding_eval_cli.py --config $Config --checkpoint .\outputs\qwen3_embedding_a4000_debug\checkpoints\best_model.pt --split test
