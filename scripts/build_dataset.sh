#!/bin/bash
# 数据集构建脚本

set -e

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${1:-configs/training/task_v1.yaml}"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# 检查依赖
check_dependencies() {
    if ! command -v python &> /dev/null; then
        log "❌ Python 未找到"
        exit 1
    fi
}

# 解析 KiCad 数据
parse_kicad_data() {
    log "🔍 解析 KiCad 数据..."

    if [ ! -d "data/raw/kicad_projects" ]; then
        log "⚠️  未找到 KiCad 项目数据，请先运行 download_kicad_data.sh"
        exit 1
    fi

    python apps/data_cli.py parse \
        --source-dir data/raw/kicad_projects \
        --output-dir data/interim/parsed_boards \
        --parallel 4
}

# 构建训练数据集
build_training_dataset() {
    log "🏗️ 构建训练数据集..."

    python apps/data_cli.py build \
        --parsed-dir data/interim/parsed_boards \
        --output-dir data/processed/task_v1 \
        --task-type LocalRouteChoice
}

# 验证数据集
validate_dataset() {
    log "✅ 验证数据集..."

    python -c "
import sys
sys.path.insert(0, '.')
from packages.data_pipeline.loaders import DatasetLoader

loader = DatasetLoader()
stats = loader.validate_dataset('data/processed/task_v1')

print('数据集统计:')
for key, value in stats.items():
    print(f'  {key}: {value}')
"
}

# 主函数
main() {
    log "🚀 开始构建数据集"

    check_dependencies
    parse_kicad_data
    build_training_dataset
    validate_dataset

    log "✅ 数据集构建完成"
}

# 参数处理
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [配置文件]"
    echo ""
    echo "参数:"
    echo "  配置文件: 训练配置文件路径 (默认: configs/training/task_v1.yaml)"
    exit 0
fi

main "$@"