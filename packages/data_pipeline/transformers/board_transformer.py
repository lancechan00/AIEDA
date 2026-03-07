"""板子数据转换器"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from PIL import Image, ImageDraw
import logging

logger = logging.getLogger(__name__)


class BoardTransformer:
    """PCB 板子数据转换器"""

    def __init__(self, default_grid_size: Tuple[int, int] = (128, 128)):
        self.default_grid_size = default_grid_size

    def board_to_geometry_grid(self, board_data: Dict[str, Any],
                              grid_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """将板子数据转换为几何栅格

        Args:
            board_data: 解析后的板子数据
            grid_size: 栅格尺寸 (height, width)

        Returns:
            几何栅格张量，形状为 (height, width, channels)
        """
        if grid_size is None:
            grid_size = self.default_grid_size

        height, width = grid_size

        # 初始化 4 个通道的栅格
        # 通道 0: 占用状态 (0=free, 1=occupied)
        # 通道 1: 层信息 (0-7 表示不同层)
        # 通道 2: 引脚密度 (0.0-1.0)
        # 通道 3: 拥塞热图 (0.0-1.0)
        grid = np.zeros((height, width, 4), dtype=np.float32)

        # 计算板子的边界
        bounds = self._calculate_board_bounds(board_data)

        # 转换各个组件
        self._fill_occupancy_from_components(grid[:, :, 0], board_data, bounds)
        self._fill_layer_info(grid[:, :, 1], board_data, bounds)
        self._fill_pin_density(grid[:, :, 2], board_data, bounds)
        self._fill_congestion_from_tracks(grid[:, :, 3], board_data, bounds)

        return grid

    def board_to_image(self, board_data: Dict[str, Any],
                      image_size: Tuple[int, int] = (512, 512)) -> Image.Image:
        """将板子数据转换为图像

        Args:
            board_data: 解析后的板子数据
            image_size: 图像尺寸 (width, height)

        Returns:
            RGB 图像
        """
        width, height = image_size

        # 创建白色背景图像
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # 计算缩放因子
        bounds = self._calculate_board_bounds(board_data)
        scale_x = width / (bounds['max_x'] - bounds['min_x']) if bounds['max_x'] > bounds['min_x'] else 1
        scale_y = height / (bounds['max_y'] - bounds['min_y']) if bounds['max_y'] > bounds['min_y'] else 1
        scale = min(scale_x, scale_y) * 0.9  # 留一些边距

        # 绘制元件
        self._draw_components(draw, board_data, bounds, scale, width, height)

        # 绘制走线
        self._draw_tracks(draw, board_data, bounds, scale, width, height)

        # 绘制过孔
        self._draw_vias(draw, board_data, bounds, scale, width, height)

        return img

    def _calculate_board_bounds(self, board_data: Dict[str, Any]) -> Dict[str, float]:
        """计算板子的边界"""
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        # 从元件位置计算边界
        for component in board_data.get('components', []):
            # 这里需要解析元件的确切位置
            # 简化的实现
            pass

        # 从走线计算边界
        for track in board_data.get('tracks', []):
            if track['type'] == 'segment':
                start_x, start_y = track['start']
                end_x, end_y = track['end']

                min_x = min(min_x, start_x, end_x)
                min_y = min(min_y, start_y, end_y)
                max_x = max(max_x, start_x, end_x)
                max_y = max(max_y, start_y, end_y)

        # 从过孔计算边界
        for via in board_data.get('vias', []):
            x, y = via['position']
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)

        # 如果没有找到边界，使用默认值
        if min_x == float('inf'):
            min_x, min_y, max_x, max_y = 0, 0, 100, 100

        return {
            'min_x': min_x, 'min_y': min_y,
            'max_x': max_x, 'max_y': max_y
        }

    def _fill_occupancy_from_components(self, occupancy_grid: np.ndarray,
                                       board_data: Dict[str, Any],
                                       bounds: Dict[str, float]) -> None:
        """从元件填充占用栅格"""
        height, width = occupancy_grid.shape

        for component in board_data.get('components', []):
            # 简化的元件占用区域计算
            # 实际实现需要解析元件的确切几何形状
            pass

    def _fill_layer_info(self, layer_grid: np.ndarray,
                        board_data: Dict[str, Any],
                        bounds: Dict[str, float]) -> None:
        """填充层信息栅格"""
        # 简化的层信息填充
        layers = board_data.get('layers', [])
        layer_mapping = {layer['id']: idx for idx, layer in enumerate(layers)}

        # 这里应该根据实际的层分配填充栅格
        pass

    def _fill_pin_density(self, pin_grid: np.ndarray,
                         board_data: Dict[str, Any],
                         bounds: Dict[str, float]) -> None:
        """填充引脚密度栅格"""
        # 简化的引脚密度计算
        # 实际实现需要解析元件引脚位置
        pass

    def _fill_congestion_from_tracks(self, congestion_grid: np.ndarray,
                                    board_data: Dict[str, Any],
                                    bounds: Dict[str, float]) -> None:
        """从走线填充拥塞热图"""
        height, width = congestion_grid.shape

        for track in board_data.get('tracks', []):
            if track['type'] == 'segment':
                start_x, start_y = track['start']
                end_x, end_y = track['end']

                # 将物理坐标转换为栅格坐标
                grid_start = self._world_to_grid((start_x, start_y), bounds, (height, width))
                grid_end = self._world_to_grid((end_x, end_y), bounds, (height, width))

                # 在栅格上绘制线段
                self._draw_line_on_grid(congestion_grid, grid_start, grid_end, value=1.0)

    def _world_to_grid(self, world_pos: Tuple[float, float],
                      bounds: Dict[str, float],
                      grid_size: Tuple[int, int]) -> Tuple[int, int]:
        """将世界坐标转换为栅格坐标"""
        x, y = world_pos
        height, width = grid_size

        # 归一化到 [0, 1]
        norm_x = (x - bounds['min_x']) / (bounds['max_x'] - bounds['min_x']) if bounds['max_x'] > bounds['min_x'] else 0.5
        norm_y = (y - bounds['min_y']) / (bounds['max_y'] - bounds['min_y']) if bounds['max_y'] > bounds['min_y'] else 0.5

        # 转换为栅格坐标
        grid_x = int(norm_x * (width - 1))
        grid_y = int(norm_y * (height - 1))

        # 确保在范围内
        grid_x = max(0, min(grid_x, width - 1))
        grid_y = max(0, min(grid_y, height - 1))

        return grid_y, grid_x  # 注意：PIL/Image 使用 (y, x) 顺序

    def _draw_line_on_grid(self, grid: np.ndarray,
                          start: Tuple[int, int],
                          end: Tuple[int, int],
                          value: float) -> None:
        """在栅格上绘制线段"""
        # 使用 Bresenham 算法绘制线段
        y1, x1 = start
        y2, x2 = end

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= y1 < grid.shape[0] and 0 <= x1 < grid.shape[1]:
                grid[y1, x1] = min(1.0, grid[y1, x1] + value)

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _draw_components(self, draw: ImageDraw.ImageDraw,
                        board_data: Dict[str, Any],
                        bounds: Dict[str, float],
                        scale: float,
                        img_width: int,
                        img_height: int) -> None:
        """绘制元件"""
        for component in board_data.get('components', []):
            # 简化的元件绘制（矩形表示）
            # 实际实现需要解析元件的确切形状和位置
            pass

    def _draw_tracks(self, draw: ImageDraw.ImageDraw,
                    board_data: Dict[str, Any],
                    bounds: Dict[str, float],
                    scale: float,
                    img_width: int,
                    img_height: int) -> None:
        """绘制走线"""
        for track in board_data.get('tracks', []):
            if track['type'] == 'segment':
                start_world = track['start']
                end_world = track['end']

                # 转换为图像坐标
                start_img = self._world_to_image(start_world, bounds, scale, img_width, img_height)
                end_img = self._world_to_image(end_world, bounds, scale, img_width, img_height)

                # 绘制线段
                draw.line([start_img, end_img], fill='blue', width=max(1, int(track.get('width', 0.25) * scale)))

    def _draw_vias(self, draw: ImageDraw.ImageDraw,
                  board_data: Dict[str, Any],
                  bounds: Dict[str, float],
                  scale: float,
                  img_width: int,
                  img_height: int) -> None:
        """绘制过孔"""
        for via in board_data.get('vias', []):
            pos_world = via['position']

            # 转换为图像坐标
            pos_img = self._world_to_image(pos_world, bounds, scale, img_width, img_height)

            # 绘制圆形表示过孔
            radius = max(2, int(via.get('size', 0.8) * scale / 2))
            draw.ellipse([
                pos_img[0] - radius, pos_img[1] - radius,
                pos_img[0] + radius, pos_img[1] + radius
            ], fill='red')

    def _world_to_image(self, world_pos: Tuple[float, float],
                       bounds: Dict[str, float],
                       scale: float,
                       img_width: int,
                       img_height: int) -> Tuple[int, int]:
        """将世界坐标转换为图像坐标"""
        x, y = world_pos

        # 归一化
        norm_x = (x - bounds['min_x']) / (bounds['max_x'] - bounds['min_x']) if bounds['max_x'] > bounds['min_x'] else 0.5
        norm_y = (y - bounds['min_y']) / (bounds['max_y'] - bounds['min_y']) if bounds['max_y'] > bounds['min_y'] else 0.5

        # 缩放和平移到图像中心
        img_x = int(norm_x * img_width * 0.9 + img_width * 0.05)  # 5% 边距
        img_y = int(norm_y * img_height * 0.9 + img_height * 0.05)

        return img_x, img_y