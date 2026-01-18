"""TranslateGemma translation engine with batch processing."""

import re
import time
from typing import Optional

import torch
from rich.console import Console
from rich.spinner import Spinner
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

from .config import TranslatorConfig

console = Console()


class TranslateGemmaEngine:
    """
    TranslateGemma model wrapper with lazy loading and batch translation.

    Supports efficient batch processing to minimize GPU overhead.
    """

    def __init__(self, config: Optional[TranslatorConfig] = None):
        """
        Initialize translator without loading model.

        Args:
            config: Translator configuration (uses defaults if None)
        """
        self.config = config or TranslatorConfig()
        self.model = None
        self.processor = None
        self.device = None
        self._model_loaded = False

    def _setup_device(self) -> None:
        """Setup CUDA/CPU device and enable optimizations."""
        if self.config.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = self.config.device

        # Enable TF32 optimizations for RTX 30xx/40xx series
        if self.device == "cuda" and self.config.enable_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

    def load_model(self, show_progress: bool = True) -> None:
        """
        Load TranslateGemma model (lazy initialization).

        Args:
            show_progress: Show loading spinner
        """
        if self._model_loaded:
            return

        self._setup_device()

        if show_progress:
            with console.status("[bold blue]Loading TranslateGemma model...", spinner="dots"):
                self._load_model_internal()
        else:
            self._load_model_internal()

        self._model_loaded = True

        if show_progress:
            device_info = self.get_device_info()
            console.print(
                f"[green]✓[/green] Model loaded on {device_info['device']}"
                + (
                    f" ({device_info['gpu_name']}, {device_info['vram_total_gb']:.1f}GB)"
                    if device_info["cuda_available"]
                    else ""
                )
            )

    def _load_model_internal(self) -> None:
        """Internal model loading logic."""
        self.processor = AutoProcessor.from_pretrained(
            self.config.model_id, cache_dir=self.config.cache_dir, use_fast=True
        )

        # Configure quantization
        quantization_config = None
        if self.device == "cuda" and self.config.quantization:
            if self.config.quantization == "4bit":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=self.config.torch_dtype,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                console.print("[dim]Using 4-bit quantization[/dim]")
            elif self.config.quantization == "8bit":
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                console.print("[dim]Using 8-bit quantization[/dim]")

        self.model = AutoModelForImageTextToText.from_pretrained(
            self.config.model_id,
            dtype=self.config.torch_dtype,
            device_map="auto",
            low_cpu_mem_usage=True,
            cache_dir=self.config.cache_dir,
            quantization_config=quantization_config,
        )

    def _has_placeholders(self, text: str) -> bool:
        """Check if text contains {placeholders}."""
        return bool(re.search(r"\{[^}]+\}", text))

    def _prepare_text_with_instructions(self, text: str) -> str:
        """
        Prepare text with instructions to preserve placeholders.

        If text contains {placeholders}, add instruction to preserve them.
        Otherwise, return text as-is.

        Args:
            text: Original text

        Returns:
            Text with instructions if needed
        """
        if not self._has_placeholders(text):
            return text

        # Add clear instruction to preserve placeholders
        instruction = (
            "[IMPORTANT: Keep all {placeholders} EXACTLY as they are. "
            "Do NOT translate words inside {curly braces}. "
            "Translate only the text outside placeholders.]\n\n"
        )

        return instruction + text

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Translate single text.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'ru')
            max_tokens: Maximum tokens to generate (uses config default if None)

        Returns:
            Translated text

        Raises:
            RuntimeError: If model not loaded
        """
        if not self._model_loaded:
            self.load_model(show_progress=False)

        max_tokens = max_tokens or self.config.max_new_tokens

        # Add instructions for preserving placeholders if found
        prepared_text = self._prepare_text_with_instructions(text)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_lang,
                        "target_lang_code": target_lang,
                        "text": prepared_text,
                    }
                ],
            }
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.device, dtype=self.config.torch_dtype)

        input_len = len(inputs["input_ids"][0])

        with torch.inference_mode():
            generation = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                use_cache=True,
            )

        generation = generation[0][input_len:]
        translation = self.processor.decode(generation, skip_special_tokens=True)

        return translation.strip()

    def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        max_tokens: Optional[int] = None,
    ) -> list[str]:
        """
        Translate multiple texts in batch for efficiency.

        Combines texts into single prompt to reduce GPU overhead.
        Automatically splits into chunks if exceeding context limit.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            max_tokens: Maximum tokens per generation

        Returns:
            List of translated texts (same order as input)

        Raises:
            RuntimeError: If model not loaded
        """
        if not self._model_loaded:
            self.load_model(show_progress=False)

        if not texts:
            return []

        if len(texts) == 1:
            return [self.translate(texts[0], source_lang, target_lang, max_tokens)]

        max_tokens = max_tokens or self.config.max_new_tokens

        # Check if any text has placeholders
        has_any_placeholders = any(self._has_placeholders(t) for t in texts)

        # Build batch prompt with numbered entries
        batch_prompt_parts = []

        # Add instruction if any text has placeholders
        if has_any_placeholders:
            batch_prompt_parts.append(
                "[IMPORTANT: Keep all {placeholders} EXACTLY as they are. "
                "Do NOT translate words inside {curly braces}. "
                "Translate only the text outside placeholders.]\n"
            )

        batch_prompt_parts.append("Translate the following texts:")
        for i, text in enumerate(texts, 1):
            batch_prompt_parts.append(f"{i}. {text}")

        batch_prompt = "\n".join(batch_prompt_parts)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_lang,
                        "target_lang_code": target_lang,
                        "text": batch_prompt,
                    }
                ],
            }
        ]

        try:
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.device, dtype=self.config.torch_dtype)

            input_len = len(inputs["input_ids"][0])

            # Check context limit (20000 tokens for TranslateGemma)
            if input_len > 18000:  # Leave room for generation
                # Split batch and retry recursively
                mid = len(texts) // 2
                left_results = self.translate_batch(
                    texts[:mid], source_lang, target_lang, max_tokens
                )
                right_results = self.translate_batch(
                    texts[mid:], source_lang, target_lang, max_tokens
                )
                return left_results + right_results

            with torch.inference_mode():
                generation = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens * len(texts),  # More tokens for batch
                    do_sample=False,
                    use_cache=True,
                )

            generation = generation[0][input_len:]
            result = self.processor.decode(generation, skip_special_tokens=True)

            # Parse numbered results
            translations = self._parse_batch_result(result, len(texts))

            # Fallback: if parsing failed, translate individually
            if len(translations) != len(texts):
                translations = [
                    self.translate(text, source_lang, target_lang, max_tokens)
                    for text in texts
                ]

            return translations

        except Exception as e:
            # Fallback to individual translation on batch error
            console.print(
                f"[yellow]Warning: Batch translation failed ({e}), "
                f"falling back to individual translation[/yellow]"
            )
            return [
                self.translate(text, source_lang, target_lang, max_tokens) for text in texts
            ]

    def _parse_batch_result(self, result: str, expected_count: int) -> list[str]:
        """
        Parse batch translation result with numbered entries.

        Args:
            result: Model output with numbered translations
            expected_count: Expected number of translations

        Returns:
            List of parsed translations
        """
        lines = result.strip().split("\n")
        translations = []

        for line in lines:
            line = line.strip()
            # Match lines like "1. Translation" or "1) Translation"
            if line and (line[0].isdigit() or line.startswith("1")):
                # Remove number prefix
                parts = line.split(".", 1) if "." in line else line.split(")", 1)
                if len(parts) == 2:
                    translations.append(parts[1].strip())
                else:
                    translations.append(line)

        return translations[:expected_count]

    def get_device_info(self) -> dict:
        """
        Get GPU/CPU device information.

        Returns:
            Dictionary with device information
        """
        info = {
            "device": self.device or "not_initialized",
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available():
            info.update(
                {
                    "gpu_name": torch.cuda.get_device_name(0),
                    "vram_total_gb": torch.cuda.get_device_properties(0).total_memory
                    / 1024**3,
                    "vram_allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
                }
            )

        return info

    def __del__(self):
        """Clean up GPU resources."""
        if torch.cuda.is_available() and self._model_loaded:
            torch.cuda.empty_cache()
