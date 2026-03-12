"""Patch 生成任务的文本序列化器。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple


class PatchPromptSerializer:
    """将局部 PCB 状态序列化为稳定文本上下文。"""

    def __init__(self, max_context_tracks: int = 16) -> None:
        self.max_context_tracks = max_context_tracks

    def serialize_track_context(
        self,
        project_name: str,
        board: Dict[str, Any],
        focus_track: Dict[str, Any],
        all_tracks: List[Dict[str, Any]],
    ) -> str:
        """序列化 segment 级上下文，供 add_trace 生成使用。"""
        net_names = self._net_map(board)
        focus_net = focus_track.get("net")
        same_net = [track for track in all_tracks if track.get("net") == focus_net]
        neighbors = self._nearest_tracks(focus_track, all_tracks, top_k=self.max_context_tracks, net_names=net_names)

        payload = {
            "task": "PatchGenerationLite",
            "project_name": project_name,
            "board_stats": self._board_stats(board),
            "focus": {
                "element_type": "segment",
                "net": focus_net,
                "net_name": net_names.get(focus_net, f"NET_{focus_net}"),
                "start": focus_track.get("start"),
                "end": focus_track.get("end"),
                "width": focus_track.get("width"),
                "layer": focus_track.get("layer"),
            },
            "same_net_track_count": len(same_net),
            "neighbor_tracks": neighbors,
            "rules": {
                "preferred_mode": "direct",
                "must_follow_net": True,
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def serialize_via_context(
        self,
        project_name: str,
        board: Dict[str, Any],
        focus_via: Dict[str, Any],
        all_tracks: List[Dict[str, Any]],
    ) -> str:
        """序列化 via 级上下文，供 add_via 生成使用。"""
        net_names = self._net_map(board)
        payload = {
            "task": "PatchGenerationLite",
            "project_name": project_name,
            "board_stats": self._board_stats(board),
            "focus": {
                "element_type": "via",
                "net": focus_via.get("net"),
                "net_name": net_names.get(focus_via.get("net"), f"NET_{focus_via.get('net')}"),
                "at": focus_via.get("at"),
                "drill": focus_via.get("drill"),
                "size": focus_via.get("size"),
                "layers": focus_via.get("layers", ["F.Cu", "B.Cu"]),
            },
            "nearby_tracks": self._nearest_tracks_for_point(
                focus_via.get("at"),
                all_tracks,
                top_k=self.max_context_tracks,
                net_names=net_names,
            ),
            "rules": {
                "via_allowed": True,
                "default_layers": ["F.Cu", "B.Cu"],
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _board_stats(self, board: Dict[str, Any]) -> Dict[str, int]:
        return {
            "num_components": len(board.get("components", [])),
            "num_tracks": len(board.get("tracks", [])),
            "num_vias": len(board.get("vias", [])),
            "num_nets": len(board.get("nets", [])),
            "num_layers": len(board.get("layers", [])),
        }

    def _nearest_tracks(
        self,
        focus_track: Dict[str, Any],
        tracks: List[Dict[str, Any]],
        top_k: int,
        net_names: Dict[Any, str],
    ) -> List[Dict[str, Any]]:
        focus_center = self._segment_center(focus_track.get("start"), focus_track.get("end"))
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for track in tracks:
            if track is focus_track or track.get("type") != "segment":
                continue
            center = self._segment_center(track.get("start"), track.get("end"))
            scored.append((self._distance(focus_center, center), track))
        scored.sort(key=lambda item: item[0])
        return [self._track_view(track, net_names) for _, track in scored[:top_k]]

    def _nearest_tracks_for_point(
        self,
        point: Any,
        tracks: List[Dict[str, Any]],
        top_k: int,
        net_names: Dict[Any, str],
    ) -> List[Dict[str, Any]]:
        if not isinstance(point, list) or len(point) < 2:
            return []
        origin = (float(point[0]), float(point[1]))
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for track in tracks:
            if track.get("type") != "segment":
                continue
            center = self._segment_center(track.get("start"), track.get("end"))
            scored.append((self._distance(origin, center), track))
        scored.sort(key=lambda item: item[0])
        return [self._track_view(track, net_names) for _, track in scored[:top_k]]

    @staticmethod
    def _track_view(track: Dict[str, Any], net_names: Dict[Any, str]) -> Dict[str, Any]:
        net_id = track.get("net")
        return {
            "net": net_id,
            "net_name": net_names.get(net_id, f"NET_{net_id}"),
            "start": track.get("start"),
            "end": track.get("end"),
            "width": track.get("width"),
            "layer": track.get("layer"),
        }

    @staticmethod
    def _net_map(board: Dict[str, Any]) -> Dict[Any, str]:
        return {
            net.get("id"): net.get("name", f"NET_{net.get('id')}")
            for net in board.get("nets", [])
        }

    @staticmethod
    def _segment_center(start: Any, end: Any) -> Tuple[float, float]:
        if not isinstance(start, list) or len(start) < 2 or not isinstance(end, list) or len(end) < 2:
            return (0.0, 0.0)
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
        return ((sx + ex) / 2.0, (sy + ey) / 2.0)

    @staticmethod
    def _distance(lhs: Tuple[float, float], rhs: Tuple[float, float]) -> float:
        dx = lhs[0] - rhs[0]
        dy = lhs[1] - rhs[1]
        return (dx * dx + dy * dy) ** 0.5
