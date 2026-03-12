"""图特征编码器。"""

from __future__ import annotations

import torch
import torch.nn as nn


class GraphFeatureEncoder(nn.Module):
    """将固定长度图特征映射到 embedding 空间。"""

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)
