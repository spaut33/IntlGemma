"""Configuration for TranslateGemma translator."""

from dataclasses import dataclass
from typing import Optional

import torch


@dataclass
class TranslatorConfig:
    """Configuration for TranslateGemma model."""

    model_id: str = "google/translategemma-4b-it"
    device: str = "auto"
    torch_dtype: torch.dtype = torch.bfloat16
    max_new_tokens: int = 200
    enable_tf32: bool = True
    cache_dir: Optional[str] = None
    quantization: Optional[str] = "4bit"  # None, "4bit", or "8bit"
