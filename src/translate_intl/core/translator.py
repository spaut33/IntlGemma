import re
import time
from pathlib import Path
from typing import Optional

import llama_cpp
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from rich.console import Console

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
        """Setup device configuration."""
        if self.config.device == "auto":
            # llama-cpp-python handles device selection based on how it was compiled
            # and n_gpu_layers parameter.
            self.device = "cuda" if llama_cpp.llama_supports_gpu_offload() else "cpu"
        else:
            self.device = self.config.device

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
            status = " (GPU acceleration enabled)" if device_info["cuda_available"] else " (CPU mode)"
            console.print(f"[green]✓[/green] Model loaded on {device_info['device']}{status}")

    def _load_model_internal(self) -> None:
        """Internal model loading logic with GGUF downloading."""
        # Download model from Hugging Face if not present
        model_path = hf_hub_download(
            repo_id=self.config.gguf_model_id,
            filename=self.config.gguf_filename,
            cache_dir=self.config.cache_dir,
        )

        # Initialize llama.cpp model
        self.model = Llama(
            model_path=model_path,
            n_gpu_layers=self.config.n_gpu_layers,
            n_ctx=self.config.n_ctx,
            verbose=False,
        )

    def _has_placeholders(self, text: str) -> bool:
        """Check if text contains any placeholders or technical-looking strings."""
        # Broad detection for curly braces (placeholders/logic)
        if "{" in text and "}" in text:
            return True
        # Detection for technical identifiers (snake_case, camelCase, dotted.names, or underscored)
        if re.search(r"\b[a-z0-9]+(?:[._][a-z0-9]+)+\b", text): # snake_case or dotted
            return True
        if re.search(r"\b[a-z0-9]+[A-Z][a-z0-9]+\b", text): # camelCase
            return True
        if "<0>" in text or "</0>" in text: # Rich text tags
            return True
        return False

    def _prepare_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """Prepare prompt for GGUF model in the expected format recommended by Ollama."""
        from .languages import get_language_name
        
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        # Official prompt format from https://ollama.com/library/translategemma
        
        rules = []
        if "{{" in text:
            rules.append("- CRITICAL: Keep all {{variable}} placeholders EXACTLY as they are. DO NOT translate the word inside the double braces. DO NOT change double braces to single braces.")
        elif "{" in text:
            rules.append("- CRITICAL: Keep all {variable} or {logic} blocks EXACTLY as they are. DO NOT translate anything inside curly braces.")
        
        if "<" in text and ">" in text:
            rules.append("- PRESERVE all rich text tags (e.g., <0>, </0>, <br/>) exactly as they are.")

        # Identification of technical IDs
        if re.search(r"\b[a-z0-9]*_[a-z0-9_]+\b", text) or re.search(r"\b[a-z]+[A-Z][a-z0-9]+\b", text):
            rules.append("- TECHNICAL IDS: Keep identifiers like snake_case, camelCase, or names_with_underscores in their original English technical format. They are system IDs, not natural language.")

        rules_instruction = ""
        if rules:
            rules_instruction = (
                "### STRICT PRESERVATION RULES:\n" + 
                "\n".join(rules) + 
                "\n\n### EXAMPLE OF PRESERVATION:\n"
                "- Source: 'Settings for {{remote_server}}'\n"
                "- Translation: 'Настройки для {{remote_server}}' (KEEP THE ID)\n\n"
            )

        # Add punctuation and formatting rules
        punctuation_rule = "- PUNCTUATION: DO NOT add a period at the end of the translation if it's missing in the source text. If the source text ends with a period, the translation MUST end with one."
        control_chars_rule = "- FORMATTING: PRESERVE all control characters like newlines (\\n) and tabs (\\t) exactly as they appear in the source text."

        # Add glossary rules
        glossary_instruction = ""
        if self.config.glossary:
            relevant_terms = {}
            for term, translation in self.config.glossary.items():
                if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
                    relevant_terms[term] = translation
            
            if relevant_terms:
                glossary_list = "\n".join([f"- '{term}' -> '{trans}'" for term, trans in relevant_terms.items()])
                glossary_instruction = f"### GLOSSARY (Use these specific translations):\n{glossary_list}\n\n"

        prompt_text = (
            f"You are a professional technical localization engine translating from {source_name} to {target_name}. "
            f"Your goal is to translate the natural language content while preserving all technical structures, variables, and IDs.\n\n"
            f"{rules_instruction}"
            f"{glossary_instruction}"
            f"### FORMATTING RULES:\n"
            f"{punctuation_rule}\n"
            f"{control_chars_rule}\n\n"
            f"Please translate the following {source_name} text into {target_name}. Return ONLY the translation:\n\n"
            f"{text}"
        )
        
        # Wrap in Gemma-it chat template for GGUF
        return (
            f"<start_of_turn>user\n"
            f"{prompt_text}<end_of_turn>\n"
            f"<start_of_turn>model\n"
        )

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Translate single text using GGUF engine.
        """
        if not self._model_loaded:
            self.load_model(show_progress=False)

        max_tokens = max_tokens or self.config.max_new_tokens
        prompt = self._prepare_prompt(text, source_lang, target_lang)

        response = self.model(
            prompt,
            max_tokens=max_tokens,
            stop=["<end_of_turn>", "\n\n"],
            echo=False,
            temperature=0.1,
        )

        translation = response["choices"][0]["text"].strip()
        
        # Restore leading/trailing whitespace if original had it
        # This ensures \n at start/end is preserved if the model didn't include it in the stripped version
        leading_ws = re.match(r"^\s*", text).group(0)
        trailing_ws = re.search(r"\s*$", text).group(0)
        
        return f"{leading_ws}{translation}{trailing_ws}"

    def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        max_tokens: Optional[int] = None,
    ) -> list[str]:
        """
        Translate multiple texts. GGUF works best with sequential processing 
        unless using specialized batching servers.
        """
        results = []
        for text in texts:
            results.append(self.translate(text, source_lang, target_lang, max_tokens))
        return results

    def _parse_batch_result(self, result: str, expected_count: int) -> list[str]:
        return []

    def get_device_info(self) -> dict:
        """
        Get GPU/CPU device information.

        Returns:
            Dictionary with device information
        """
        gpu_supported = llama_cpp.llama_supports_gpu_offload()
        
        info = {
            "device": self.device or "not_initialized",
            "cuda_available": gpu_supported,
        }

        if gpu_supported and self.model:
            # We can get some info from llama.cpp but it's more limited without torch
            info.update({
                "gpu_support": "Yes (llama-cpp-python with CUDA/Metal/etc.)",
                "n_gpu_layers": self.config.n_gpu_layers
            })

        return info

    def __del__(self):
        """Clean up resources."""
        # llama-cpp handles its own cleanup, but we can clear the model ref
        self.model = None
