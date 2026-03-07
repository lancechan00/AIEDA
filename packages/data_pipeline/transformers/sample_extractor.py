"""第一阶段样本提取器。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SampleExtractor:
    """从真实 track 段生成确定性弱标注。"""

    def __init__(
        self,
        region_size: int = 64,
        world_window: float = 20.0,
        max_samples_per_board: int = 64,
    ) -> None:
        self.region_size = region_size
        self.world_window = world_window
        self.max_samples_per_board = max_samples_per_board

    def extract_samples_from_project(
        self,
        project_data: Dict[str, Any],
        task_type: str = "LocalRouteChoiceLite",
    ) -> List[Dict[str, Any]]:
        if task_type != "LocalRouteChoiceLite":
            raise ValueError("第一阶段当前只支持 `LocalRouteChoiceLite`")

        board = project_data["board"]
        tracks = [track for track in board.get("tracks", []) if track.get("type") == "segment"]
        samples: List[Dict[str, Any]] = []

        for track_index, track in enumerate(tracks[: self.max_samples_per_board]):
            sample = self._create_route_choice_sample(project_data, track, tracks, track_index)
            if sample is not None:
                samples.append(sample)

        return samples

    def _create_route_choice_sample(
        self,
        project_data: Dict[str, Any],
        track: Dict[str, Any],
        all_tracks: List[Dict[str, Any]],
        track_index: int,
    ) -> Optional[Dict[str, Any]]:
        start = tuple(track["start"])
        end = tuple(track["end"])
        local_bounds = self._window_bounds(start, self.world_window)

        geometry = np.zeros((self.region_size, self.region_size, 4), dtype=np.float32)

        # channel 0: 其他走线占用
        for context_track in all_tracks:
            if context_track is track:
                continue
            self._draw_segment_on_grid(
                geometry[:, :, 0],
                context_track["start"],
                context_track["end"],
                local_bounds,
                1.0,
            )

        # channel 1: 同 net 走线占用
        for context_track in all_tracks:
            if context_track is track or context_track.get("net") != track.get("net"):
                continue
            self._draw_segment_on_grid(
                geometry[:, :, 1],
                context_track["start"],
                context_track["end"],
                local_bounds,
                1.0,
            )

        # channel 2: 起点 marker
        self._mark_point(geometry[:, :, 2], start, local_bounds, value=1.0, radius=2)

        # channel 3: 终点 marker，作为弱监督目标提示
        self._mark_point(geometry[:, :, 3], end, local_bounds, value=1.0, radius=2)

        label = self._direction_from_segment(start, end, local_bounds)
        image = self._geometry_to_rgb(geometry)

        return {
            "geometry": geometry.tolist(),
            "image": image.tolist(),
            "label": label,
            "task_type": "LocalRouteChoiceLite",
            "metadata": {
                "project_name": project_data["project_name"],
                "board_id": project_data["project_name"],
                "track_index": track_index,
                "net_code": track.get("net"),
            },
        }

    def _window_bounds(self, center: Tuple[float, float], window_size: float) -> Dict[str, float]:
        half = window_size / 2.0
        return {
            "min_x": center[0] - half,
            "max_x": center[0] + half,
            "min_y": center[1] - half,
            "max_y": center[1] + half,
        }

    def _direction_from_segment(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        bounds: Dict[str, float],
    ) -> str:
        start_row, start_col = self._world_to_grid(start, bounds)
        end_row, end_col = self._world_to_grid(end, bounds)
        d_row = end_row - start_row
        d_col = end_col - start_col

        if d_row == 0 and d_col == 0:
            return "stop"
        if abs(d_col) >= abs(d_row):
            return "right" if d_col > 0 else "left"
        return "down" if d_row > 0 else "up"

    def _draw_segment_on_grid(
        self,
        grid: np.ndarray,
        start: List[float],
        end: List[float],
        bounds: Dict[str, float],
        value: float,
    ) -> None:
        start_row, start_col = self._world_to_grid(tuple(start), bounds)
        end_row, end_col = self._world_to_grid(tuple(end), bounds)

        row, col = start_row, start_col
        d_col = abs(end_col - col)
        d_row = abs(end_row - row)
        step_col = 1 if col < end_col else -1
        step_row = 1 if row < end_row else -1
        error = d_col - d_row

        while True:
            if 0 <= row < self.region_size and 0 <= col < self.region_size:
                grid[row, col] = max(grid[row, col], value)
            if row == end_row and col == end_col:
                break
            doubled = error * 2
            if doubled > -d_row:
                error -= d_row
                col += step_col
            if doubled < d_col:
                error += d_col
                row += step_row

    def _mark_point(
        self,
        grid: np.ndarray,
        point: Tuple[float, float],
        bounds: Dict[str, float],
        value: float,
        radius: int,
    ) -> None:
        row, col = self._world_to_grid(point, bounds)
        for row_offset in range(-radius, radius + 1):
            for col_offset in range(-radius, radius + 1):
                rr = row + row_offset
                cc = col + col_offset
                if 0 <= rr < self.region_size and 0 <= cc < self.region_size:
                    grid[rr, cc] = value

    def _world_to_grid(self, point: Tuple[float, float], bounds: Dict[str, float]) -> Tuple[int, int]:
        x, y = point
        norm_x = (x - bounds["min_x"]) / max(bounds["max_x"] - bounds["min_x"], 1e-6)
        norm_y = (y - bounds["min_y"]) / max(bounds["max_y"] - bounds["min_y"], 1e-6)
        col = int(np.clip(norm_x, 0.0, 1.0) * (self.region_size - 1))
        row = int(np.clip(norm_y, 0.0, 1.0) * (self.region_size - 1))
        return row, col

    def _geometry_to_rgb(self, geometry: np.ndarray) -> np.ndarray:
        rgb = np.zeros((self.region_size, self.region_size, 3), dtype=np.uint8)
        rgb[:, :, 0] = np.clip(geometry[:, :, 0] * 255, 0, 255).astype(np.uint8)
        rgb[:, :, 1] = np.clip(geometry[:, :, 2] * 255, 0, 255).astype(np.uint8)
        rgb[:, :, 2] = np.clip(geometry[:, :, 3] * 255, 0, 255).astype(np.uint8)
        return rgb
