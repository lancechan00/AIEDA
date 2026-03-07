"""Janus 第一阶段实验后端占位。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class JanusAdapter(nn.Module):
    """仅保留统一接口和确定性多模态占位逻辑。"""

    supports_training = False

    def __init__(
        self,
        modalities: Optional[List[str]] = None,
        num_classes: int = 5,
        task_type: str = "LocalRouteChoiceLite",
        model_name: str = "deepseek-ai/janus-1.3b",
        **_: Any,
    ) -> None:
        super().__init__()
        self.modalities = modalities or ["geometry", "image"]
        self.num_classes = num_classes
        self.task_type = task_type
        self.model_name = model_name

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        geometry = inputs.get("geometry")
        image = inputs.get("image")

        if geometry is None:
            raise ValueError("Janus 占位后端至少需要 `geometry`")

        batch_size = geometry.shape[0]
        logits = torch.zeros(batch_size, self.num_classes, device=geometry.device)

        occupancy = geometry[:, 0]
        center_row = occupancy[:, occupancy.shape[-2] // 2, :]
        center_col = occupancy[:, :, occupancy.shape[-1] // 2]

        logits[:, 0] = -center_col[:, : center_col.shape[-1] // 2].sum(dim=-1)
        logits[:, 1] = -center_col[:, center_col.shape[-1] // 2 :].sum(dim=-1)
        logits[:, 2] = -center_row[:, : center_row.shape[-1] // 2].sum(dim=-1)
        logits[:, 3] = -center_row[:, center_row.shape[-1] // 2 :].sum(dim=-1)

        if image is not None:
            # 轻量融合: 用亮度均值调节 stop 类，保持确定性。
            logits[:, 4] = image.mean(dim=(1, 2, 3))
        else:
            logits[:, 4] = 0.0

        return {"logits": logits}

    def get_trainable_params(self) -> List[torch.nn.Parameter]:
        return []

    def get_modality_info(self) -> Dict[str, Any]:
        return {
            "supported_modalities": ["geometry", "image"],
            "current_modalities": self.modalities,
            "task_type": self.task_type,
            "model_name": self.model_name,
            "supports_training": False,
        }