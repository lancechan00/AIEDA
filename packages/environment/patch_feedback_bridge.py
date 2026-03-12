"""Patch 执行反馈桥接接口（第一版占位 + Mock 闭环验证）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PatchFeedbackResult:
    accepted: bool
    errors: List[str] = field(default_factory=list)
    drc_violations: List[Dict[str, Any]] = field(default_factory=list)
    board_snapshot: Dict[str, Any] = field(default_factory=dict)


def _mock_validate_patch(patch: Dict[str, Any]) -> List[str]:
    """Mock 模式下对 Patch 进行结构校验，返回错误列表，空则通过。"""
    errors: List[str] = []
    if "op" not in patch:
        errors.append("missing op")
    elif patch["op"] not in {"add_trace", "add_via", "remove_item", "modify_item"}:
        errors.append(f"unknown op: {patch.get('op')}")
    if "net_id" not in patch:
        errors.append("missing net_id")
    params = patch.get("params")
    if not isinstance(params, dict):
        errors.append("params must be dict")
    else:
        op = patch.get("op")
        if op == "add_trace":
            if "layer" not in params:
                errors.append("add_trace requires params.layer")
            if "points" not in params:
                errors.append("add_trace requires params.points")
            elif not isinstance(params["points"], (list, tuple)) or len(params["points"]) < 2:
                errors.append("add_trace params.points must have at least 2 points")
        elif op == "add_via":
            if "at" not in params:
                errors.append("add_via requires params.at")
            if "layers" not in params:
                errors.append("add_via requires params.layers")
    return errors


class PatchFeedbackBridge:
    """定义未来接入 EDA 闭环时的统一接口；支持 Mock 模式用于闭环验证。"""

    def __init__(self, use_mock: bool = False) -> None:
        """use_mock=True 时，对 Patch 做结构校验并返回 accepted 状态，不执行真实 EDA。"""
        self.use_mock = use_mock

    def apply_patch(self, patch: Dict[str, Any]) -> PatchFeedbackResult:
        """执行或校验 Patch。Mock 模式下仅做结构检查。"""
        if self.use_mock:
            errors = _mock_validate_patch(patch)
            return PatchFeedbackResult(
                accepted=len(errors) == 0,
                errors=errors,
                drc_violations=[],
                board_snapshot={},
            )
        return PatchFeedbackResult(
            accepted=False,
            errors=["EDA bridge not connected yet"],
            drc_violations=[],
            board_snapshot={},
        )
