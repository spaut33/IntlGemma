"""Configuration for TranslateGemma translator."""

from dataclasses import dataclass


@dataclass
class TranslatorConfig:
    """Configuration for TranslateGemma model."""

    model_id: str = "google/translategemma-4b-it"
    device: str = "auto"
    max_new_tokens: int = 200
    enable_tf32: bool = True
    cache_dir: str | None = None
    # GGUF settings
    gguf_model_id: str = "NikolayKozloff/translategemma-4b-it-Q8_0-GGUF"
    gguf_filename: str = "translategemma-4b-it-q8_0.gguf"
    n_gpu_layers: int = -1  # -1 means all layers on GPU
    n_ctx: int = 4096
    glossary: dict[str, str] | None = None
