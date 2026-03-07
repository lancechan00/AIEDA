# Backends Package

from .tiny_baseline import TinyBaselineAdapter
from .deepseek_vl import DeepSeekVLAdapter
from .janus import JanusAdapter

__all__ = ['TinyBaselineAdapter', 'DeepSeekVLAdapter', 'JanusAdapter']


def get_backend(backend_name: str):
    """获取模型后端"""
    backends = {
        'tiny_baseline': TinyBaselineAdapter,
        'deepseek_vl': DeepSeekVLAdapter,
        'janus': JanusAdapter
    }

    if backend_name not in backends:
        raise ValueError(f"未知的模型后端: {backend_name}. 支持的后端: {list(backends.keys())}")

    return backends[backend_name]