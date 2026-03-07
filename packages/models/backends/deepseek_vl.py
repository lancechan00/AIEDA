"""DeepSeek-VL 第一阶段实验后端占位。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class DeepSeekVLAdapter(nn.Module):
    """仅保留接口和确定性推理占位，不进入正式训练主链。"""

    supports_training = False

    def __init__(
        self,
        modalities: Optional[List[str]] = None,
        num_classes: int = 5,
        task_type: str = "LocalRouteChoiceLite",
        model_name: str = "deepseek-ai/deepseek-vl-7b-chat",
        **_: Any,
    ) -> None:
        super().__init__()
        self.modalities = modalities or ["geometry", "image"]
        self.num_classes = num_classes
        self.task_type = task_type
        self.model_name = model_name

    def forward(self, inputs: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        geometry = inputs.get("geometry")
        if geometry is None:
            raise ValueError("DeepSeek-VL 占位后端至少需要 `geometry`")

        if geometry.dim() != 4:
            raise ValueError("`geometry` 需要是 [B, C, H, W]")

        batch_size = geometry.shape[0]
        logits = torch.zeros(batch_size, self.num_classes, device=geometry.device)

        # 一个稳定的启发式占位：比较中心点上下左右四个方向的占用强度。
        occupancy = geometry[:, 0]
        height = occupancy.shape[-2]
        width = occupancy.shape[-1]
        cy = height // 2
        cx = width // 2

        up = occupancy[:, :cy, cx].sum(dim=-1)
        down = occupancy[:, cy + 1 :, cx].sum(dim=-1)
        left = occupancy[:, cy, :cx].sum(dim=-1)
        right = occupancy[:, cy, cx + 1 :].sum(dim=-1)
        scores = torch.stack([-up, -down, -left, -right], dim=-1)

        logits[:, :4] = scores
        logits[:, 4] = -torch.min(scores, dim=-1).values

        return {
            "logits": logits,
            "backend_mode": torch.tensor(0, device=geometry.device),
        }

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