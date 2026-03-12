"""PCB 多模态到文本条件的 adapter。"""

from __future__ import annotations

from typing import Dict


class PcbMultimodalAdapter:
    """将结构化 PCB 样本适配为生成模型输入模板。"""

    def format_prompt(self, instruction: str, context_text: str) -> str:
        return (
            "### Instruction\n"
            f"{instruction.strip()}\n\n"
            "### Context\n"
            f"{context_text.strip()}\n\n"
            "### Patch\n"
        )

    def format_training_pair(self, instruction: str, context_text: str, target_patch: str) -> Dict[str, str]:
        prompt = self.format_prompt(instruction=instruction, context_text=context_text)
        return {
            "prompt": prompt,
            "target": target_patch.strip(),
        }
