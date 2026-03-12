"""Patch 执行反馈桥接接口（第一版占位）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PatchFeedbackResult:
    accepted: bool
    errors: List[str] = field(default_factory=list)
    drc_violations: List[Dict[str, Any]] = field(default_factory=list)
    board_snapshot: Dict[str, Any] = field(default_factory=dict)


class PatchFeedbackBridge:
    """定义未来接入 EDA 闭环时的统一接口。"""

    def apply_patch(self, patch: Dict[str, Any]) -> PatchFeedbackResult:
        """第一版只提供接口定义，不执行真实 EDA 操作。"""
        return PatchFeedbackResult(
            accepted=False,
            errors=["EDA bridge not connected yet"],
            drc_violations=[],
            board_snapshot={},
        )
