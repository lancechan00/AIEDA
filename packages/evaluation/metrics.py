"""最小评估指标。"""

from __future__ import annotations

from typing import Dict

import torch


def compute_metrics(logits: torch.Tensor, labels: torch.Tensor, top_k: int = 3) -> Dict[str, float]:
    """计算第一阶段分类指标。"""
    if logits.ndim != 2:
        raise ValueError("`logits` 需要是 [N, C]")
    if labels.ndim != 1:
        raise ValueError("`labels` 需要是 [N]")

    predictions = torch.argmax(logits, dim=-1)
    accuracy = (predictions == labels).float().mean().item()

    k = min(top_k, logits.shape[-1])
    topk = torch.topk(logits, k=k, dim=-1).indices
    topk_accuracy = (topk == labels.unsqueeze(-1)).any(dim=-1).float().mean().item()

    loss = torch.nn.functional.cross_entropy(logits, labels).item()

    return {
        "loss": float(loss),
        "accuracy": float(accuracy),
        "top_3_accuracy": float(topk_accuracy),
    }
