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


def compute_retrieval_metrics(similarity: torch.Tensor) -> Dict[str, float]:
    """计算 graph-text 检索指标。

    约定 similarity[i, i] 为正样本，其余为负样本。
    """
    if similarity.ndim != 2:
        raise ValueError("`similarity` 需要是 [N, N] 或 [N, M] 二维矩阵")
    if similarity.shape[0] == 0 or similarity.shape[1] == 0:
        raise ValueError("`similarity` 不能为空")

    if similarity.shape[0] != similarity.shape[1]:
        n = min(similarity.shape[0], similarity.shape[1])
        similarity = similarity[:n, :n]

    n_items = similarity.shape[0]
    positive_scores = similarity.diag()
    sorted_indices = torch.argsort(similarity, dim=1, descending=True)
    target_indices = torch.arange(n_items, device=similarity.device).unsqueeze(1)
    ranks = (sorted_indices == target_indices).nonzero(as_tuple=False)[:, 1] + 1

    recall_at_1 = (ranks <= 1).float().mean().item()
    recall_at_3 = (ranks <= min(3, n_items)).float().mean().item()
    recall_at_5 = (ranks <= min(5, n_items)).float().mean().item()
    reciprocal_ranks = (1.0 / ranks.float()).mean().item()

    negative_mask = ~torch.eye(n_items, dtype=torch.bool, device=similarity.device)
    negative_scores = similarity[negative_mask].view(n_items, -1)
    hardest_negative = negative_scores.max(dim=1).values
    positive_negative_gap = (positive_scores - hardest_negative).mean().item()

    return {
        "recall_at_1": float(recall_at_1),
        "recall_at_3": float(recall_at_3),
        "recall_at_5": float(recall_at_5),
        "mrr": float(reciprocal_ranks),
        "avg_pos_neg_gap": float(positive_negative_gap),
    }
