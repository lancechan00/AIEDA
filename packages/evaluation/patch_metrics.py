"""Patch DSL 生成评估。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple


REQUIRED_TOP_LEVEL_FIELDS = {"op", "net_id", "params"}


def parse_patch_text(patch_text: str) -> Tuple[bool, Dict[str, Any] | None]:
    """尝试解析 patch 文本。"""
    try:
        parsed = json.loads(patch_text)
    except json.JSONDecodeError:
        return False, None
    if not isinstance(parsed, dict):
        return False, None
    return True, parsed


def patch_has_required_fields(patch_obj: Dict[str, Any]) -> bool:
    if not REQUIRED_TOP_LEVEL_FIELDS.issubset(set(patch_obj.keys())):
        return False
    if not isinstance(patch_obj.get("params"), dict):
        return False
    return True


def patch_action_exact_match(pred: Dict[str, Any], gold: Dict[str, Any]) -> bool:
    return pred == gold


def compute_patch_metrics(predictions: List[str], targets: List[str]) -> Dict[str, float]:
    if len(predictions) != len(targets):
        raise ValueError("predictions 与 targets 数量必须一致")
    if not predictions:
        return {
            "parse_success_rate": 0.0,
            "field_completeness_rate": 0.0,
            "action_exact_match": 0.0,
        }

    parse_success = 0
    complete_fields = 0
    exact_match = 0

    for pred_text, target_text in zip(predictions, targets):
        pred_ok, pred_obj = parse_patch_text(pred_text)
        target_ok, target_obj = parse_patch_text(target_text)
        if pred_ok:
            parse_success += 1
            assert pred_obj is not None
            if patch_has_required_fields(pred_obj):
                complete_fields += 1

        if pred_ok and target_ok and pred_obj is not None and target_obj is not None:
            if patch_action_exact_match(pred_obj, target_obj):
                exact_match += 1

    total = float(len(predictions))
    return {
        "parse_success_rate": parse_success / total,
        "field_completeness_rate": complete_fields / total,
        "action_exact_match": exact_match / total,
    }
