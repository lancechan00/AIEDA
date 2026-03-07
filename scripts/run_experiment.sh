#!/bin/bash
# 运行实验脚本

set -e

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${1:-configs/training/task_v1.yaml}"
EXPERIMENT_NAME="${2:-default_experiment}"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# 检查依赖和数据
check_prerequisites() {
    # 检查 Python
    if ! command -v python &> /dev/null; then
        log "❌ Python 未找到"
        exit 1
    fi

    # 检查配置文件
    if [ ! -f "$CONFIG_FILE" ]; then
        log "❌ 配置文件不存在: $CONFIG_FILE"
        exit 1
    fi

    # 检查数据集
    if [ ! -d "data/processed/task_v1" ]; then
        log "⚠️  数据集不存在，运行构建脚本..."
        ./scripts/build_dataset.sh
    fi
}

# 运行训练
run_training() {
    log "🚀 开始训练实验: $EXPERIMENT_NAME"

    python apps/train_cli.py \
        --config "$CONFIG_FILE" \
        --experiment-name "$EXPERIMENT_NAME" \
        --output-dir "outputs/experiments/$EXPERIMENT_NAME"
}

# 运行评估
run_evaluation() {
    log "📊 开始评估实验: $EXPERIMENT_NAME"

    PREDICTIONS_DIR="outputs/experiments/$EXPERIMENT_NAME/predictions"
    GROUND_TRUTH_FILE="data/processed/task_v1/test_labels.json"

    if [ -d "$PREDICTIONS_DIR" ]; then
        python apps/eval_cli.py metrics \
            --predictions "$PREDICTIONS_DIR/test_predictions.json" \
            --ground-truth "$GROUND_TRUTH_FILE" \
            --task-type LocalRouteChoice \
            --output-file "outputs/experiments/$EXPERIMENT_NAME/evaluation_results.json"
    else
        log "⚠️  未找到预测结果，跳过评估"
    fi
}

# 生成报告
generate_report() {
    log "📄 生成实验报告: $EXPERIMENT_NAME"

    python apps/eval_cli.py analyze \
        --results-dir "outputs/experiments/$EXPERIMENT_NAME" \
        --output-dir "outputs/reports" \
        --experiment-type full_evaluation
}

# 主函数
main() {
    log "🧪 开始运行实验: $EXPERIMENT_NAME"

    check_prerequisites
    run_training
    run_evaluation
    generate_report

    log "✅ 实验运行完成"
    log "📁 结果保存在: outputs/experiments/$EXPERIMENT_NAME"
}

# 参数处理
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [配置文件] [实验名称]"
    echo ""
    echo "参数:"
    echo "  配置文件: 训练配置文件路径 (默认: configs/training/task_v1.yaml)"
    echo "  实验名称: 实验名称 (默认: default_experiment)"
    echo ""
    echo "示例:"
    echo "  $0 configs/training/task_v1.yaml my_experiment"
    exit 0
fi

main "$@"