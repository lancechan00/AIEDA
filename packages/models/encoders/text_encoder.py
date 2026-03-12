"""文本编码器：Qwen 或 hash fallback。"""

from __future__ import annotations

import hashlib
from typing import List

import numpy as np
import torch
import torch.nn as nn


class HashTextEncoder(nn.Module):
    """无需外部模型的稳定文本编码器，供 smoke test 与离线调试。"""

    def __init__(self, output_dim: int = 1024) -> None:
        super().__init__()
        self.output_dim = output_dim

    def forward(self, texts: List[str]) -> torch.Tensor:
        vectors = [self._encode_single(text) for text in texts]
        return torch.stack(vectors, dim=0)

    def _encode_single(self, text: str) -> torch.Tensor:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)
        random_state = np.random.default_rng(seed)
        vector = random_state.normal(loc=0.0, scale=1.0, size=self.output_dim).astype(np.float32)
        return torch.from_numpy(vector)


class QwenTextEncoder(nn.Module):
    """基于 transformers 的 Qwen embedding 文本塔。"""

    def __init__(self, model_name: str, max_length: int = 256) -> None:
        super().__init__()
        from transformers import AutoModel, AutoTokenizer  # 局部导入，避免无依赖环境提前失败

        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)

    def forward(self, texts: List[str]) -> torch.Tensor:
        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,
        )
        encoded = {key: value.to(self.model.device) for key, value in encoded.items()}
        outputs = self.model(**encoded)
        hidden = outputs.last_hidden_state
        attention_mask = encoded["attention_mask"]
        eos_indices = attention_mask.sum(dim=1) - 1
        batch_indices = torch.arange(hidden.shape[0], device=hidden.device)
        embeddings = hidden[batch_indices, eos_indices, :]
        return embeddings
