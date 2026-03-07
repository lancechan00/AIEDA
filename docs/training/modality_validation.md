# 模态验证策略

## 概述

本策略定义了如何系统性地验证和比较不同模态组合的效果，确保 v1 阶段能够有效识别最有价值的输入模态和模型后端组合。

## 验证框架

### 验证目标

1. **模态重要性排序**: 确定哪些模态对任务性能贡献最大
2. **组合效果评估**: 分析模态间的互补性和冗余性
3. **模型后端适配**: 比较不同模型对各类模态的处理能力
4. **计算效率分析**: 评估模态复杂度与性能的权衡

### 验证原则

1. **可控变量**: 每次只改变一个模态或模型后端
2. **公平比较**: 使用相同的训练设置和评估指标
3. **统计显著性**: 确保结果差异具有统计意义
4. **可重现性**: 所有实验都有确定的随机种子

## 实验设计

### 1. 模态消融实验 (Modality Ablation)

#### 实验设置

##### 基础配置
- **模型后端**: 固定使用 Tiny Baseline (确保可控)
- **任务**: LocalRouteChoice (作为基础验证任务)
- **数据集**: 相同的数据集划分
- **训练设置**: 相同的超参数和训练流程

##### 模态配置
```python
MODALITY_CONFIGS = [
    {
        'name': 'geometry_only',
        'modalities': ['geometry_grid'],
        'expected_params': '~5M'
    },
    {
        'name': 'image_only',
        'modalities': ['board_image'],
        'expected_params': '~10M'
    },
    {
        'name': 'geometry_image',
        'modalities': ['geometry_grid', 'board_image'],
        'expected_params': '~15M'
    },
    {
        'name': 'geometry_image_text',
        'modalities': ['geometry_grid', 'board_image', 'text_rules'],
        'expected_params': '~16M'
    },
    {
        'name': 'all_modalities',
        'modalities': ['geometry_grid', 'board_image', 'text_rules', 'graph_structure'],
        'expected_params': '~20M'
    }
]
```

#### 实验流程

##### 训练阶段
```python
def run_ablation_experiment(config, dataset, num_runs=3):
    """运行单次消融实验"""

    results = []

    for run in range(num_runs):
        # 设置随机种子
        set_seed(run)

        # 创建模型
        model = create_model_for_config(config)

        # 训练模型
        trained_model = train_model(model, dataset, config)

        # 评估模型
        metrics = evaluate_model(trained_model, dataset['test'])

        results.append(metrics)

    # 计算平均结果和方差
    avg_results = calculate_average_results(results)
    std_results = calculate_std_results(results)

    return {
        'config': config,
        'avg_metrics': avg_results,
        'std_metrics': std_results,
        'individual_runs': results
    }
```

##### 评估指标
- **主要指标**: 验证集准确率、测试集准确率
- **收敛指标**: 达到最佳性能所需的训练轮数
- **稳定性指标**: 多次运行结果的标准差

### 2. 模型后端对比实验 (Backend Comparison)

#### 实验设置

##### 固定模态配置
- **模态组合**: geometry + image (基于消融实验结果选择)
- **任务**: 三种任务 (LocalRouteChoice, NetRegionMatch, MockPatchPrediction)
- **数据集**: 相同划分
- **训练预算**: 相同的计算资源限制

##### 后端配置
```python
BACKEND_CONFIGS = [
    {
        'name': 'tiny_baseline',
        'model_class': TinyBaselineAdapter,
        'expected_time': '2-4 hours',
        'expected_memory': '4GB'
    },
    {
        'name': 'deepseek_vl',
        'model_class': DeepSeekVLAdapter,
        'expected_time': '8-12 hours',
        'expected_memory': '16GB'
    },
    {
        'name': 'janus',
        'model_class': JanusAdapter,
        'expected_time': '12-24 hours',
        'expected_memory': '24GB'
    }
]
```

#### 实验流程

##### 多任务评估
```python
def run_backend_comparison(backend_configs, modality_config, tasks):
    """运行后端对比实验"""

    comparison_results = {}

    for backend_config in backend_configs:
        backend_results = {}

        for task in tasks:
            # 为每个任务训练模型
            task_results = train_and_evaluate_task(
                backend_config, modality_config, task
            )

            backend_results[task['name']] = task_results

        comparison_results[backend_config['name']] = backend_results

    return comparison_results
```

### 3. 模态交互实验 (Modality Interaction)

#### 实验设置

##### 交互类型
- **互补性**: 模态组合是否带来超加性收益
- **冗余性**: 模态间的信息重叠程度
- **鲁棒性**: 单个模态缺失时的性能下降

##### 实验设计
```python
def analyze_modality_interactions(full_model, ablated_models):
    """分析模态间的交互效果"""

    interactions = {}

    # 计算互补性
    full_performance = evaluate_model(full_model)
    individual_performances = {
        name: evaluate_model(model)
        for name, model in ablated_models.items()
    }

    # 超加性检验
    expected_additive = sum(individual_performances.values()) / len(individual_performances)
    actual_synergy = full_performance - expected_additive

    interactions['synergy'] = actual_synergy
    interactions['complementary_ratio'] = actual_synergy / full_performance

    # 冗余性分析
    correlations = calculate_modality_correlations(individual_performances)
    interactions['redundancy_matrix'] = correlations

    return interactions
```

## 统计验证方法

### 显著性检验

#### t检验应用
```python
def perform_statistical_tests(results_a, results_b, test_type='paired_ttest'):
    """对实验结果进行统计检验"""

    if test_type == 'paired_ttest':
        # 配对 t 检验 (适用于相同数据集上的不同模型)
        t_stat, p_value = stats.ttest_rel(results_a, results_b)

    elif test_type == 'independent_ttest':
        # 独立 t 检验 (适用于不同数据集)
        t_stat, p_value = stats.ttest_ind(results_a, results_b)

    # Cohen's d 效应量
    effect_size = calculate_cohens_d(results_a, results_b)

    return {
        'test_type': test_type,
        't_statistic': t_stat,
        'p_value': p_value,
        'effect_size': effect_size,
        'significant': p_value < 0.05,
        'effect_magnitude': interpret_effect_size(effect_size)
    }
```

#### 多重比较校正
```python
def correct_multiple_comparisons(p_values, method='bonferroni'):
    """多重比较的 p 值校正"""

    if method == 'bonferroni':
        # Bonferroni 校正
        corrected_p = np.minimum(p_values * len(p_values), 1.0)

    elif method == 'holm_bonferroni':
        # Holm-Bonferroni 方法
        sorted_indices = np.argsort(p_values)
        corrected_p = np.ones_like(p_values)

        for i, idx in enumerate(sorted_indices):
            corrected_p[idx] = min(p_values[idx] * (len(p_values) - i), 1.0)

    return corrected_p
```

### 置信区间估计

#### 自举法
```python
def bootstrap_confidence_interval(results, num_bootstrap=1000, confidence=0.95):
    """使用自举法计算置信区间"""

    bootstrap_samples = []

    for _ in range(num_bootstrap):
        # 有放回采样
        sample = np.random.choice(results, size=len(results), replace=True)
        bootstrap_samples.append(np.mean(sample))

    # 计算置信区间
    lower_percentile = (1 - confidence) / 2 * 100
    upper_percentile = (1 + confidence) / 2 * 100

    ci_lower = np.percentile(bootstrap_samples, lower_percentile)
    ci_upper = np.percentile(bootstrap_samples, upper_percentile)

    return {
        'mean': np.mean(results),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'confidence_level': confidence
    }
```

## 实验执行策略

### 批次执行

#### 队列管理
```python
class ExperimentQueue:
    def __init__(self, max_concurrent=2):
        self.queue = []
        self.running = []
        self.completed = []
        self.max_concurrent = max_concurrent

    def add_experiment(self, experiment_config):
        """添加实验到队列"""
        self.queue.append(experiment_config)

    def run_next_batch(self):
        """运行下一批实验"""

        # 计算可以启动的实验数量
        available_slots = self.max_concurrent - len(self.running)

        # 启动新实验
        for _ in range(min(available_slots, len(self.queue))):
            experiment = self.queue.pop(0)
            self.running.append(self.start_experiment(experiment))

        # 检查完成状态
        self.check_completed_experiments()

    def start_experiment(self, config):
        """启动单个实验"""
        # 在后台启动实验进程
        process = subprocess.Popen([
            'python', 'run_experiment.py',
            '--config', json.dumps(config)
        ])

        return {
            'config': config,
            'process': process,
            'start_time': time.time()
        }
```

### 资源管理

#### GPU 分配
```python
def allocate_gpus_for_experiments(experiments, available_gpus=[0, 1, 2, 3]):
    """为实验分配 GPU 资源"""

    gpu_assignments = {}

    # 按模型大小排序实验
    sorted_experiments = sorted(
        experiments,
        key=lambda x: x['config']['expected_memory'],
        reverse=True
    )

    for experiment in sorted_experiments:
        # 为大模型分配更多 GPU
        memory_requirement = experiment['config']['expected_memory']

        if memory_requirement > 16:  # 大模型
            assigned_gpus = available_gpus[:2]  # 分配 2 个 GPU
            available_gpus = available_gpus[2:]
        else:  # 小模型
            assigned_gpus = [available_gpus[0]]  # 分配 1 个 GPU
            available_gpus = available_gpus[1:]

        gpu_assignments[experiment['id']] = assigned_gpus

    return gpu_assignments
```

## 结果分析和报告

### 性能分析

#### 综合评分
```python
def calculate_composite_score(metrics, weights):
    """计算综合性能评分"""

    composite_score = 0

    for metric_name, weight in weights.items():
        if metric_name in metrics:
            # 归一化指标值
            normalized_value = normalize_metric(metrics[metric_name], metric_name)
            composite_score += normalized_value * weight

    return composite_score
```

#### 效率分析
```python
def analyze_efficiency(results):
    """分析训练效率"""

    efficiency_metrics = {}

    for result in results:
        # 计算每单位时间的性能提升
        performance_per_hour = result['final_accuracy'] / result['training_hours']

        # 计算每单位计算资源的性能
        performance_per_gpu_hour = result['final_accuracy'] / (
            result['gpu_hours']
        )

        efficiency_metrics[result['config']['name']] = {
            'performance_per_hour': performance_per_hour,
            'performance_per_gpu_hour': performance_per_gpu_hour,
            'cost_effectiveness': performance_per_gpu_hour / result['config']['cost']
        }

    return efficiency_metrics
```

### 可视化报告

#### 结果对比图表
```python
def generate_comparison_plots(results):
    """生成对比分析图表"""

    # 模态消融对比
    plot_modality_ablation(results['ablation'])

    # 模型后端对比
    plot_backend_comparison(results['backends'])

    # 效率分析
    plot_efficiency_analysis(results['efficiency'])

    # 统计显著性
    plot_significance_tests(results['statistical_tests'])
```

#### 交互式报告
```python
def create_interactive_report(results, output_path):
    """创建交互式 HTML 报告"""

    # 使用 plotly 或 bokeh 创建交互式图表
    figures = create_interactive_figures(results)

    # 生成 HTML 报告
    html_content = generate_html_report(figures, results)

    with open(output_path, 'w') as f:
        f.write(html_content)
```

## 决策制定

### 模态选择决策

#### 选择标准
1. **性能贡献**: 模态对任务准确率的提升程度
2. **计算成本**: 模态处理增加的计算开销
3. **数据可用性**: 模态数据的获取和标注难度
4. **泛化潜力**: 模态对新任务的适用性

#### 决策矩阵
```python
def create_decision_matrix(modality_results):
    """创建模态选择决策矩阵"""

    criteria = ['performance_gain', 'computational_cost', 'data_availability', 'generalization_potential']

    decision_matrix = {}

    for modality in modality_results:
        scores = {}
        for criterion in criteria:
            scores[criterion] = calculate_criterion_score(modality, criterion)

        # 加权总分
        weights = {'performance_gain': 0.4, 'computational_cost': 0.2,
                  'data_availability': 0.2, 'generalization_potential': 0.2}

        total_score = sum(scores[criterion] * weights[criterion] for criterion in criteria)

        decision_matrix[modality] = {
            'criterion_scores': scores,
            'total_score': total_score,
            'recommendation': 'include' if total_score > 0.7 else 'exclude'
        }

    return decision_matrix
```

### 模型后端选择决策

#### 选择标准
1. **任务适应性**: 后端对 PCB 任务的性能表现
2. **开发效率**: 适配和维护的难易程度
3. **部署成本**: 推理和服务的资源需求
4. **扩展性**: 支持新任务和模态的能力

#### 成本效益分析
```python
def cost_benefit_analysis(backend_results):
    """对模型后端进行成本效益分析"""

    analysis = {}

    for backend in backend_results:
        costs = {
            'development_cost': estimate_development_cost(backend),
            'training_cost': backend['training_cost'],
            'inference_cost': backend['inference_cost_per_sample']
        }

        benefits = {
            'performance_gain': backend['accuracy'] - baseline_accuracy,
            'development_speed': backend['time_to_first_result'],
            'maintenance_effort': backend['maintenance_complexity']
        }

        # 计算投资回报率
        roi = calculate_roi(benefits, costs)

        analysis[backend['name']] = {
            'costs': costs,
            'benefits': benefits,
            'roi': roi,
            'recommendation': 'adopt' if roi > 1.5 else 'consider_alternatives'
        }

    return analysis
```

## 持续监控和迭代

### 实验追踪

#### MLflow 集成
```python
import mlflow

def setup_experiment_tracking(experiment_name):
    """设置实验追踪"""

    mlflow.set_experiment(experiment_name)

    # 记录实验元数据
    mlflow.log_param('modalities', modality_config)
    mlflow.log_param('backend', backend_name)
    mlflow.log_param('task', task_name)

def log_experiment_results(metrics, artifacts):
    """记录实验结果"""

    # 记录指标
    for metric_name, value in metrics.items():
        mlflow.log_metric(metric_name, value)

    # 记录 artifacts
    for artifact_name, path in artifacts.items():
        mlflow.log_artifact(path, artifact_name)
```

### 自动回归测试

#### 性能基线监控
```python
def monitor_performance_baselines(current_results, baseline_results):
    """监控性能基线"""

    alerts = []

    for metric in baseline_results:
        current_value = current_results.get(metric, 0)
        baseline_value = baseline_results[metric]['value']
        threshold = baseline_results[metric]['threshold']

        if abs(current_value - baseline_value) > threshold:
            alerts.append({
                'metric': metric,
                'current': current_value,
                'baseline': baseline_value,
                'deviation': abs(current_value - baseline_value),
                'threshold': threshold
            })

    return alerts
```

这个验证策略确保了 v1 阶段能够系统性地探索模态空间，为后续版本提供坚实的科学基础。通过严格的实验设计和统计验证，我们能够做出数据驱动的决策，确定最有前景的技术方向。