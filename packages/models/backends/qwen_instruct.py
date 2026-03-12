"""本地 Qwen-Instruct 生成后端（含离线 fallback）。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class _CharTokenizer:
    """离线最小 tokenizer，保障无权重环境也可跑通链路。"""

    def __init__(self) -> None:
        self.pad_token_id = 0
        self.eos_token_id = 1
        self._id2char: Dict[int, str] = {}

    def _token_id(self, ch: str) -> int:
        token_id = 2 + (ord(ch) % 253)
        if token_id not in self._id2char:
            self._id2char[token_id] = ch
        return token_id

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        token_ids = [self._token_id(ch) for ch in text]
        if add_special_tokens:
            token_ids.append(self.eos_token_id)
        return token_ids

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        chars: List[str] = []
        for token_id in token_ids:
            if skip_special_tokens and token_id in {self.pad_token_id, self.eos_token_id}:
                continue
            chars.append(self._id2char.get(token_id, ""))
        return "".join(chars)

    def batch_decode(self, batch_token_ids: List[List[int]], skip_special_tokens: bool = True) -> List[str]:
        return [self.decode(token_ids, skip_special_tokens=skip_special_tokens) for token_ids in batch_token_ids]

    def __call__(
        self,
        texts: List[str],
        truncation: bool = True,
        max_length: Optional[int] = None,
        padding: bool = True,
        return_tensors: str = "pt",
        add_special_tokens: bool = False,
    ) -> Dict[str, torch.Tensor]:
        encoded = []
        for text in texts:
            token_ids = self.encode(text, add_special_tokens=add_special_tokens)
            if truncation and max_length is not None:
                token_ids = token_ids[:max_length]
            encoded.append(token_ids)

        max_len = max((len(ids) for ids in encoded), default=1)
        if max_length is not None and padding:
            max_len = min(max_len, max_length)
        padded: List[List[int]] = []
        masks: List[List[int]] = []
        for token_ids in encoded:
            if max_length is not None:
                token_ids = token_ids[:max_length]
            pad_len = max_len - len(token_ids)
            padded.append(token_ids + [self.pad_token_id] * max(0, pad_len))
            masks.append([1] * len(token_ids) + [0] * max(0, pad_len))

        if return_tensors != "pt":
            raise ValueError("仅支持 return_tensors='pt'")
        return {
            "input_ids": torch.tensor(padded, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.long),
        }

    @property
    def vocab_size(self) -> int:
        return 256


class _TinyCausalLM(nn.Module):
    """离线最小自回归模型。"""

    def __init__(self, vocab_size: int, hidden_dim: int = 256) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)
        self.lm_head = nn.Linear(hidden_dim, vocab_size)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        del attention_mask
        hidden = self.embedding(input_ids)
        hidden, _ = self.gru(hidden)
        logits = self.lm_head(hidden)
        output: Dict[str, torch.Tensor] = {"logits": logits}
        if labels is not None:
            loss = torch.nn.functional.cross_entropy(
                logits.reshape(-1, logits.shape[-1]),
                labels.reshape(-1),
                ignore_index=-100,
            )
            output["loss"] = loss
        return output

    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 64,
        eos_token_id: int = 1,
        pad_token_id: int = 0,
    ) -> torch.Tensor:
        generated = input_ids
        for _ in range(max_new_tokens):
            outputs = self.forward(generated)
            next_token = torch.argmax(outputs["logits"][:, -1, :], dim=-1, keepdim=True)
            generated = torch.cat([generated, next_token], dim=1)
            if (next_token == eos_token_id).all():
                break
        if generated.shape[1] < input_ids.shape[1] + max_new_tokens:
            pad_len = input_ids.shape[1] + max_new_tokens - generated.shape[1]
            padding = torch.full((generated.shape[0], pad_len), pad_token_id, device=generated.device)
            generated = torch.cat([generated, padding], dim=1)
        return generated


class QwenInstructAdapter(nn.Module):
    """PatchGenerationLite 的文本生成后端。"""

    supports_training = True

    def __init__(
        self,
        task_type: str = "PatchGenerationLite",
        text_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        load_pretrained: bool = False,
        local_files_only: bool = True,
        **_: Any,
    ) -> None:
        super().__init__()
        if task_type != "PatchGenerationLite":
            raise ValueError("`qwen_instruct` 当前只支持 `PatchGenerationLite`")
        self.task_type = task_type
        self.text_model_name = text_model_name
        self._use_hf_backend = False

        self.tokenizer: Any
        self.model: nn.Module

        if load_pretrained:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer

                self.tokenizer = AutoTokenizer.from_pretrained(
                    text_model_name,
                    trust_remote_code=True,
                    local_files_only=local_files_only,
                )
                if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                self.model = AutoModelForCausalLM.from_pretrained(
                    text_model_name,
                    trust_remote_code=True,
                    local_files_only=local_files_only,
                )
                self._use_hf_backend = True
                logger.info("QwenInstructAdapter 使用预训练模型: %s", text_model_name)
            except Exception as exc:  # pragma: no cover - 仅在缺权重时触发
                logger.warning("加载预训练模型失败，回退到离线最小模型: %s", exc)
                self.tokenizer = _CharTokenizer()
                self.model = _TinyCausalLM(vocab_size=self.tokenizer.vocab_size)
        else:
            self.tokenizer = _CharTokenizer()
            self.model = _TinyCausalLM(vocab_size=self.tokenizer.vocab_size)
            logger.info("QwenInstructAdapter 使用离线最小模型（未加载预训练权重）")

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        if self._use_hf_backend:
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            result = {"logits": outputs.logits}
            if outputs.loss is not None:
                result["loss"] = outputs.loss
            return result
        return self.model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_new_tokens: int = 192,
    ) -> torch.Tensor:
        if self._use_hf_backend:
            return self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        return self.model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )

    def get_trainable_params(self) -> List[torch.nn.Parameter]:
        return list(self.parameters())

    def get_modality_info(self) -> Dict[str, Any]:
        return {
            "supported_modalities": ["text"],
            "task_type": self.task_type,
            "text_model_name": self.text_model_name,
            "use_pretrained_backend": self._use_hf_backend,
        }
