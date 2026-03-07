"""第一阶段最小 `tiny_baseline`。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class ConvEncoder(nn.Module):
    """共享的轻量卷积编码器。"""

    def __init__(self, in_channels: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(64, hidden_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        return self.net(tensor)


class TinyBaselineAdapter(nn.Module):
    """用于 `LocalRouteChoiceLite` 的可训练基线。"""

    supports_training = True

    def __init__(
        self,
        modalities: Optional[List[str]] = None,
        num_classes: int = 5,
        hidden_dim: int = 64,
        task_type: str = "LocalRouteChoiceLite",
        geometry_channels: int = 4,
        image_channels: int = 3,
        **_: Any,
    ) -> None:
        super().__init__()

        if task_type != "LocalRouteChoiceLite":
            raise ValueError("`tiny_baseline` 当前只支持 `LocalRouteChoiceLite`")

        self.modalities = modalities or ["geometry", "image"]
        self.task_type = task_type

        self.encoders = nn.ModuleDict()
        feature_dims: List[int] = []

        if "geometry" in self.modalities:
            self.encoders["geometry"] = ConvEncoder(geometry_channels, hidden_dim)
            feature_dims.append(hidden_dim)

        if "image" in self.modalities:
            self.encoders["image"] = ConvEncoder(image_channels, hidden_dim)
            feature_dims.append(hidden_dim)

        if not feature_dims:
            raise ValueError("至少需要一种输入模态")

        fused_dim = sum(feature_dims)
        self.fusion = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.ReLU(inplace=True),
        )
        self.classifier = nn.Linear(hidden_dim, num_classes)

        logger.info("TinyBaseline 初始化完成: modalities=%s num_classes=%s", self.modalities, num_classes)

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        features: List[torch.Tensor] = []
        for modality in self.modalities:
            if modality not in inputs:
                continue
            features.append(self.encoders[modality](inputs[modality]))

        if not features:
            raise ValueError("输入 batch 中缺少模型所需模态")

        fused = features[0] if len(features) == 1 else self.fusion(torch.cat(features, dim=-1))
        logits = self.classifier(fused)
        return {"logits": logits, "features": fused}

    def get_trainable_params(self) -> List[torch.nn.Parameter]:
        return list(self.parameters())

    def get_modality_info(self) -> Dict[str, Any]:
        return {
            "supported_modalities": ["geometry", "image"],
            "current_modalities": self.modalities,
            "task_type": self.task_type,
        }