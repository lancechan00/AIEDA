"""模型适配器"""

from typing import Dict, List, Any, Optional, Type
import torch
import torch.nn as nn
import logging

from ..backends import get_backend

logger = logging.getLogger(__name__)


class ModelAdapter:
    """统一的模型适配器接口"""

    def __init__(self, backend_name: str, backend_config: Dict[str, Any]):
        """初始化适配器

        Args:
            backend_name: 后端名称 ('tiny_baseline', 'deepseek_vl', 'janus')
            backend_config: 后端配置
        """
        self.backend_name = backend_name
        self.backend_config = backend_config

        # 获取后端类
        backend_class = get_backend(backend_name)

        # 初始化后端模型
        self.model = backend_class(**backend_config)

        logger.info(f"模型适配器初始化: {backend_name}")

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """前向传播

        Args:
            inputs: 输入字典

        Returns:
            输出字典
        """
        return self.model(inputs)

    def get_trainable_params(self) -> List[torch.nn.Parameter]:
        """获取可训练参数"""
        return self.model.get_trainable_params()

    def get_modality_info(self) -> Dict[str, Any]:
        """获取模态信息"""
        return self.model.get_modality_info()

    def save(self, path: str) -> None:
        """保存模型"""
        torch.save({
            'backend_name': self.backend_name,
            'backend_config': self.backend_config,
            'model_state_dict': self.model.state_dict(),
        }, path)
        logger.info(f"模型已保存到: {path}")

    @classmethod
    def load(cls, path: str, device: Optional[str] = None) -> 'ModelAdapter':
        """加载模型"""
        checkpoint = torch.load(path, map_location=device)

        backend_name = checkpoint['backend_name']
        backend_config = checkpoint['backend_config']

        adapter = cls(backend_name, backend_config)
        adapter.model.load_state_dict(checkpoint['model_state_dict'])

        logger.info(f"模型已从 {path} 加载")
        return adapter

    def to(self, device: torch.device) -> 'ModelAdapter':
        """移动到设备"""
        self.model = self.model.to(device)
        return self

    def train(self) -> 'ModelAdapter':
        """设置为训练模式"""
        self.model.train()
        return self

    def eval(self) -> 'ModelAdapter':
        """设置为评估模式"""
        self.model.eval()
        return self

    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """调用接口"""
        return self.forward(inputs)


class ModalityValidationRunner:
    """模态验证运行器"""

    def __init__(self, task_type: str = 'LocalRouteChoice'):
        self.task_type = task_type
        self.results = {}

    def setup_experiments(self, modality_configs: List[Dict[str, Any]],
                         backend_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """设置验证实验

        Args:
            modality_configs: 模态配置列表
            backend_configs: 后端配置列表

        Returns:
            实验配置列表
        """
        experiments = []

        for modality_config in modality_configs:
            for backend_config in backend_configs:
                experiment = {
                    'modality_config': modality_config,
                    'backend_config': backend_config,
                    'experiment_name': f"{modality_config['name']}_{backend_config['name']}"
                }
                experiments.append(experiment)

        return experiments

    def run_experiment(self, experiment_config: Dict[str, Any],
                      train_loader, val_loader,
                      num_epochs: int = 10) -> Dict[str, Any]:
        """运行单个实验

        Args:
            experiment_config: 实验配置
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            num_epochs: 训练轮数

        Returns:
            实验结果
        """
        experiment_name = experiment_config['experiment_name']

        logger.info(f"开始实验: {experiment_name}")

        # 创建模型适配器
        modality_config = experiment_config['modality_config']
        backend_config = experiment_config['backend_config']

        # 合并配置
        full_backend_config = {
            **backend_config,
            'modalities': modality_config['modalities'],
            'task_type': self.task_type
        }

        adapter = ModelAdapter(backend_config['name'], full_backend_config)

        # 简化的训练循环（实际应该使用 Trainer 类）
        optimizer = torch.optim.AdamW(adapter.get_trainable_params(), lr=1e-3)
        criterion = self._get_criterion()

        best_val_metric = float('-inf')
        training_history = []

        for epoch in range(num_epochs):
            # 训练
            adapter.train()
            train_loss = self._train_epoch(adapter, train_loader, optimizer, criterion)

            # 验证
            adapter.eval()
            val_loss, val_metrics = self._validate_epoch(adapter, val_loader, criterion)

            # 记录历史
            epoch_result = {
                'epoch': epoch,
                'train_loss': train_loss,
                'val_loss': val_loss,
                'val_metrics': val_metrics
            }
            training_history.append(epoch_result)

            # 保存最佳模型
            val_acc = val_metrics.get('accuracy', 0)
            if val_acc > best_val_metric:
                best_val_metric = val_acc

            logger.info(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")

        result = {
            'experiment_name': experiment_name,
            'modality_config': modality_config,
            'backend_config': backend_config,
            'best_val_metric': best_val_metric,
            'training_history': training_history,
            'final_metrics': training_history[-1]['val_metrics'] if training_history else {}
        }

        self.results[experiment_name] = result
        return result

    def _get_criterion(self):
        """获取损失函数"""
        if self.task_type == 'LocalRouteChoice':
            return nn.CrossEntropyLoss()
        elif self.task_type == 'NetRegionMatch':
            return nn.MSELoss()
        else:
            return nn.CrossEntropyLoss()

    def _train_epoch(self, model, train_loader, optimizer, criterion):
        """训练一个 epoch"""
        total_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()

            outputs = model(batch)
            loss = criterion(outputs['logits'], batch['label'])

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def _validate_epoch(self, model, val_loader, criterion):
        """验证一个 epoch"""
        total_loss = 0.0
        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for batch in val_loader:
                outputs = model(batch)
                loss = criterion(outputs['logits'], batch['label'])

                total_loss += loss.item()

                # 收集预测和标签
                if self.task_type == 'LocalRouteChoice':
                    predictions = torch.argmax(outputs['logits'], dim=-1)
                else:
                    predictions = outputs['logits']

                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(batch['label'].cpu().numpy())

        # 计算指标
        metrics = self._compute_metrics(all_predictions, all_labels)

        return total_loss / len(val_loader), metrics

    def _compute_metrics(self, predictions, labels):
        """计算评估指标"""
        # 简化的指标计算
        if self.task_type == 'LocalRouteChoice':
            accuracy = (predictions == labels).mean()
            return {'accuracy': accuracy}
        elif self.task_type == 'NetRegionMatch':
            mse = ((predictions - labels) ** 2).mean()
            return {'mse': mse}
        else:
            accuracy = (predictions == labels).mean()
            return {'accuracy': accuracy}

    def get_summary_report(self) -> Dict[str, Any]:
        """生成汇总报告"""
        if not self.results:
            return {}

        # 按模态分组结果
        modality_groups = {}
        backend_groups = {}

        for result in self.results.values():
            modality_name = result['modality_config']['name']
            backend_name = result['backend_config']['name']

            if modality_name not in modality_groups:
                modality_groups[modality_name] = []
            modality_groups[modality_name].append(result['best_val_metric'])

            if backend_name not in backend_groups:
                backend_groups[backend_name] = []
            backend_groups[backend_name].append(result['best_val_metric'])

        # 计算统计
        summary = {
            'total_experiments': len(self.results),
            'modality_performance': {
                name: {
                    'mean': sum(scores) / len(scores),
                    'max': max(scores),
                    'min': min(scores)
                }
                for name, scores in modality_groups.items()
            },
            'backend_performance': {
                name: {
                    'mean': sum(scores) / len(scores),
                    'max': max(scores),
                    'min': min(scores)
                }
                for name, scores in backend_groups.items()
            },
            'best_overall': max(result['best_val_metric'] for result in self.results.values()),
            'best_experiment': max(self.results.keys(),
                                 key=lambda k: self.results[k]['best_val_metric'])
        }

        return summary