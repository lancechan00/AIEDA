"""KiCad 文件解析器"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class KiCadParser:
    """KiCad PCB 和 netlist 文件解析器"""

    def __init__(self):
        self.supported_extensions = {'.kicad_pcb', '.net'}

    def parse_projects(self, source_dir: str, output_dir: str, max_workers: int = 4) -> None:
        """批量解析 KiCad 项目

        Args:
            source_dir: KiCad 项目源目录
            output_dir: 解析结果输出目录
            max_workers: 最大并行工作数
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 查找所有 KiCad 项目
        projects = self._find_kicad_projects(source_path)

        logger.info(f"找到 {len(projects)} 个 KiCad 项目")

        # 并行解析项目
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for project_path in projects:
                future = executor.submit(
                    self._parse_single_project,
                    project_path,
                    output_path
                )
                futures.append(future)

            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"解析项目失败: {e}")

    def _find_kicad_projects(self, source_dir: Path) -> List[Path]:
        """查找所有包含 KiCad 文件的项目目录"""
        projects = []

        # 递归查找 .kicad_pcb 文件
        for kicad_file in source_dir.rglob('*.kicad_pcb'):
            project_dir = kicad_file.parent
            if self._is_valid_kicad_project(project_dir):
                projects.append(project_dir)

        return list(set(projects))  # 去重

    def _is_valid_kicad_project(self, project_dir: Path) -> bool:
        """检查是否为有效的 KiCad 项目。"""
        return any(project_dir.glob('*.kicad_pcb'))

    def _parse_single_project(self, project_dir: Path, output_dir: Path) -> None:
        """解析单个 KiCad 项目"""
        project_name = project_dir.name

        try:
            # 查找主要文件
            pcb_file = next(project_dir.glob('*.kicad_pcb'))
            net_file = next(project_dir.glob('*.net'), None)

            logger.info(f"解析项目: {project_name}")

            # 解析 PCB 文件
            board_data = self._parse_pcb_file(pcb_file)

            # `.net` 可选；没有时退化为从 PCB net 表构造最小 netlist。
            if net_file is not None:
                netlist_data = self._parse_netlist_file(net_file)
            else:
                netlist_data = {
                    'nets': [
                        {
                            'code': net['id'],
                            'name': net['name'],
                            'content': '',
                        }
                        for net in board_data.get('nets', [])
                    ],
                    'components': [],
                }

            # 合并数据
            project_data = {
                'project_name': project_name,
                'board': board_data,
                'netlist': netlist_data,
                'metadata': {
                    'source_files': {
                        'pcb': str(pcb_file),
                        'netlist': str(net_file) if net_file is not None else None
                    },
                    'parsed_at': str(Path(output_dir) / f"{project_name}.json")
                }
            }

            # 保存解析结果
            output_file = output_dir / f"{project_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            logger.info(f"项目 {project_name} 解析完成")

        except Exception as e:
            logger.error(f"解析项目 {project_name} 失败: {e}")
            raise

    def _parse_pcb_file(self, pcb_file: Path) -> Dict[str, Any]:
        """解析 KiCad PCB 文件

        这里实现一个简化的解析器，实际项目中可能需要使用专门的 KiCad 解析库
        """
        with open(pcb_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简化的正则表达式解析
        board_data = {
            'general': self._parse_general_info(content),
            'layers': self._parse_layers(content),
            'components': self._parse_components(content),
            'tracks': self._parse_tracks(content),
            'vias': self._parse_vias(content),
            'nets': self._parse_nets(content)
        }

        return board_data

    def _parse_general_info(self, content: str) -> Dict[str, Any]:
        """解析通用信息"""
        # 提取板子尺寸等信息
        # 这里是简化的实现
        return {
            'version': '20221018',  # 默认版本
            'generator': 'kicad_parser_v1'
        }

    def _parse_layers(self, content: str) -> List[Dict[str, Any]]:
        """解析层信息"""
        layers = []

        # 简化的层解析
        layer_patterns = [
            r'\((\d+)\s+"([^"]+)"\s+(\w+)\)',  # (0 "F.Cu" signal)
        ]

        for pattern in layer_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                layer_id, layer_name, layer_type = match
                layers.append({
                    'id': int(layer_id),
                    'name': layer_name,
                    'type': layer_type
                })

        return layers

    def _parse_components(self, content: str) -> List[Dict[str, Any]]:
        """解析元件信息"""
        components = []

        # 简化的元件解析
        module_pattern = r'\(module\s+"([^"]+)"\s+\(layer\s+"([^"]+)"\)(.*?)\)\)'
        matches = re.findall(module_pattern, content, re.DOTALL)

        for match in matches:
            module_name, layer, module_content = match
            components.append({
                'name': module_name,
                'layer': layer,
                'content': module_content.strip()
            })

        return components

    def _parse_tracks(self, content: str) -> List[Dict[str, Any]]:
        """解析走线信息"""
        tracks = []

        # 简化的走线解析
        segment_pattern = r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(\d+)\)\)'
        matches = re.findall(segment_pattern, content)

        for match in matches:
            start_x, start_y, end_x, end_y, width, layer, net = match
            tracks.append({
                'type': 'segment',
                'start': [float(start_x), float(start_y)],
                'end': [float(end_x), float(end_y)],
                'width': float(width),
                'layer': layer,
                'net': int(net)
            })

        return tracks

    def _parse_vias(self, content: str) -> List[Dict[str, Any]]:
        """解析过孔信息"""
        vias = []

        # 简化的过孔解析
        via_pattern = r'\(via\s+\(at\s+([\d.-]+)\s+([\d.-]+)\)\s+\(size\s+([\d.-]+)\)\s+\(drill\s+([\d.-]+)\)\s+\(layers\s+"([^"]+)"\s+"([^"]+)"\)\s+\(net\s+(\d+)\)\)'
        matches = re.findall(via_pattern, content)

        for match in matches:
            x, y, size, drill, layer1, layer2, net = match
            vias.append({
                'position': [float(x), float(y)],
                'size': float(size),
                'drill': float(drill),
                'layers': [layer1, layer2],
                'net': int(net)
            })

        return vias

    def _parse_nets(self, content: str) -> List[Dict[str, Any]]:
        """解析网络信息"""
        nets = []

        # 简化的网络解析
        net_pattern = r'\(net\s+(\d+)\s+"([^"]+)"\)'
        matches = re.findall(net_pattern, content)

        for match in matches:
            net_id, net_name = match
            nets.append({
                'id': int(net_id),
                'name': net_name
            })

        return nets

    def _parse_netlist_file(self, net_file: Path) -> Dict[str, Any]:
        """解析 KiCad netlist 文件"""
        with open(net_file, 'r', encoding='utf-8') as f:
            content = f.read()

        netlist_data = {
            'nets': self._parse_netlist_nets(content),
            'components': self._parse_netlist_components(content)
        }

        return netlist_data

    def _parse_netlist_nets(self, content: str) -> List[Dict[str, Any]]:
        """解析 netlist 中的网络"""
        nets = []

        # 简化的网络解析
        net_pattern = r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]+)"\)(.*?)\)'
        matches = re.findall(net_pattern, content, re.DOTALL)

        for match in matches:
            code, name, net_content = match
            nets.append({
                'code': int(code),
                'name': name,
                'content': net_content.strip()
            })

        return nets

    def _parse_netlist_components(self, content: str) -> List[Dict[str, Any]]:
        """解析 netlist 中的元件"""
        components = []

        # 简化的元件解析
        comp_pattern = r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]+)"\)\s+\(footprint\s+"([^"]+)"\)(.*?)\)'
        matches = re.findall(comp_pattern, content, re.DOTALL)

        for match in matches:
            ref, value, footprint, comp_content = match
            components.append({
                'ref': ref,
                'value': value,
                'footprint': footprint,
                'content': comp_content.strip()
            })

        return components


class MockKiCadGenerator:
    """用于测试的 Mock KiCad 数据生成器"""

    def generate_mock_board(self, complexity: str = 'simple') -> Dict[str, Any]:
        """生成模拟的板子数据"""

        if complexity == 'simple':
            return self._generate_simple_board()
        elif complexity == 'medium':
            return self._generate_medium_board()
        else:
            return self._generate_complex_board()

    def _generate_simple_board(self) -> Dict[str, Any]:
        """生成简单的模拟板子"""
        return {
            'general': {'version': '20221018'},
            'layers': [
                {'id': 0, 'name': 'F.Cu', 'type': 'signal'},
                {'id': 31, 'name': 'B.Cu', 'type': 'signal'}
            ],
            'components': [
                {'name': 'U1', 'layer': 'F.Cu'},
                {'name': 'C1', 'layer': 'F.Cu'}
            ],
            'tracks': [
                {'type': 'segment', 'start': [10, 10], 'end': [20, 10],
                 'width': 0.25, 'layer': 'F.Cu', 'net': 1}
            ],
            'vias': [],
            'nets': [
                {'id': 1, 'name': 'GND'},
                {'id': 2, 'name': 'VCC'}
            ]
        }

    def _generate_medium_board(self) -> Dict[str, Any]:
        """生成中等复杂度的模拟板子"""
        # 实现略
        return self._generate_simple_board()

    def _generate_complex_board(self) -> Dict[str, Any]:
        """生成复杂模拟板子"""
        # 实现略
        return self._generate_simple_board()