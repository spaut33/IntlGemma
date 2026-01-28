"""Translation service orchestrating file operations and model inference."""

import json
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from translate_intl.core.config import TranslatorConfig
from translate_intl.core.translator import TranslateGemmaEngine
from translate_intl.models.translation import MissingKeysReport
from translate_intl.services.file_service import TranslationFileService
from translate_intl.utils.json_handler import flatten_dict, unflatten_dict
from translate_intl.utils.progress import create_translation_progress, print_translation_summary
from translate_intl.utils.validators import (
    format_validation_error,
    validate_translation,
)

console = Console()


class TranslationService:
    """High-level service for translating next-intl projects."""

    def __init__(
        self, messages_dir: Path, translator_config: Optional[TranslatorConfig] = None
    ):
        """
        Initialize translation service.

        Args:
            messages_dir: Path to messages directory
            translator_config: Translator configuration (uses defaults if None)
        """
        self.file_service = TranslationFileService(messages_dir)
        self.translator = TranslateGemmaEngine(translator_config)

    def load_glossary(self, glossary_path: Path) -> None:
        """
        Load glossary from a JSON file.

        Args:
            glossary_path: Path to glossary JSON file
        """
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                glossary = json.load(f)
            self.translator.config.glossary = glossary
            console.print(f"[green]✓[/green] Loaded glossary with {len(glossary)} terms")
        except Exception as e:
            console.print(f"[red]Error loading glossary from {glossary_path}: {e}[/red]")

    def translate_all(
        self,
        source_lang: str,
        target_langs: list[str],
        max_tokens: int = 200,
        batch_size: int = 20,
        nested: Optional[bool] = None,
        glossary_path: Optional[Path] = None,
    ) -> None:
        """
        Translate all keys to target languages.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            max_tokens: Maximum tokens per generation
            batch_size: Number of texts to translate in one batch
            nested: Whether to use nested structure (False for flat). If None, auto-detected.
            glossary_path: Path to glossary JSON file (optional)
        """
        if glossary_path:
            self.load_glossary(glossary_path)

        # Load model once for all languages
        self.translator.load_model(show_progress=True)

        source_file = self.file_service.load_language_file(source_lang)
        
        # Use provided nested flag or auto-detect from source
        is_nested = nested if nested is not None else source_file.is_nested
        
        flat_source = flatten_dict(source_file.data, nested=is_nested)
        all_keys = list(flat_source.keys())

        for target_lang in target_langs:
            console.print(f"\n[bold cyan]Translating to {target_lang}...[/bold cyan]")
            self._translate_language(
                source_lang=source_lang,
                target_lang=target_lang,
                keys_to_translate=all_keys,
                source_data=source_file.data,
                max_tokens=max_tokens,
                batch_size=batch_size,
                nested=is_nested,
            )

    def translate_missing(
        self,
        source_lang: str,
        target_langs: list[str],
        max_tokens: int = 200,
        batch_size: int = 20,
        nested: Optional[bool] = None,
        glossary_path: Optional[Path] = None,
    ) -> None:
        """
        Translate only missing keys to target languages.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            max_tokens: Maximum tokens per generation
            batch_size: Number of texts to translate in one batch
            nested: Whether to use nested structure (False for flat). If None, auto-detected.
            glossary_path: Path to glossary JSON file (optional)
        """
        if glossary_path:
            self.load_glossary(glossary_path)

        # Load model once for all languages
        self.translator.load_model(show_progress=True)

        source_file = self.file_service.load_language_file(source_lang)
        
        # Use provided nested flag or auto-detect from source
        is_nested = nested if nested is not None else source_file.is_nested

        for target_lang in target_langs:
            console.print(f"\n[bold cyan]Checking {target_lang}...[/bold cyan]")

            # Find missing keys
            report = self.file_service.find_missing_keys(source_lang, target_lang)

            if not report.missing_keys:
                console.print(f"[green]✓[/green] {target_lang}: No missing keys")
                continue

            console.print(
                f"[yellow]Found {len(report.missing_keys)} missing keys[/yellow]"
            )

            self._translate_language(
                source_lang=source_lang,
                target_lang=target_lang,
                keys_to_translate=report.missing_keys,
                source_data=source_file.data,
                max_tokens=max_tokens,
                batch_size=batch_size,
                nested=is_nested,
            )

    def _translate_language(
        self,
        source_lang: str,
        target_lang: str,
        keys_to_translate: list[str],
        source_data: dict,
        max_tokens: int,
        batch_size: int,
        nested: bool = True,
    ) -> None:
        """
        Translate keys for a single language with batch processing.

        Args:
            source_lang: Source language code
            target_lang: Target language code
            keys_to_translate: List of flat keys to translate
            source_data: Source language nested data
            max_tokens: Maximum tokens per generation
            batch_size: Batch size for translation
            nested: Whether to use nested structure
        """
        if not keys_to_translate:
            return

        # Load or create target file
        try:
            target_file = self.file_service.load_language_file(target_lang)
            target_data = target_file.data
        except FileNotFoundError:
            target_file = self.file_service.create_language_file(target_lang)
            target_data = {}

        flat_source = flatten_dict(source_data, nested=nested)
        start_time = time.time()
        translated_count = 0

        with create_translation_progress() as progress:
            task = progress.add_task(
                f"[cyan]Translating {target_lang}...", total=len(keys_to_translate)
            )

            # Process in batches
            for i in range(0, len(keys_to_translate), batch_size):
                batch_keys = keys_to_translate[i : i + batch_size]
                batch_texts = [flat_source[key] for key in batch_keys]

                try:
                    # Batch translation
                    translations = self.translator.translate_batch(
                        texts=batch_texts,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        max_tokens=max_tokens,
                    )

                    # Validate and update target data
                    for key, original, translation in zip(batch_keys, batch_texts, translations):
                        # Validate translation
                        validation = validate_translation(
                            original, translation, strict=False
                        )

                        value_to_save = translation
                        if not validation.is_valid:
                            # Log validation error
                            error_msg = format_validation_error(
                                key, original, translation, validation
                            )
                            console.print(f"[yellow]⚠ {error_msg}[/yellow]")

                            if validation.errors:
                                console.print(
                                    f"[red]  Validation errors found for '{key}'. Using original text as fallback.[/red]"
                                )
                                value_to_save = original

                        # Update target data
                        target_data = self.file_service.set_value_by_flat_key(
                            target_data, key, value_to_save, nested=nested
                        )
                        translated_count += 1

                    progress.update(task, advance=len(batch_keys))

                except Exception as e:
                    console.print(
                        f"[red]Error translating batch {i}-{i+len(batch_keys)}: {e}[/red]"
                    )
                    # Continue with next batch
                    progress.update(task, advance=len(batch_keys))

        # Save updated target file
        target_file.data = target_data
        self.file_service.save_language_file(target_file, backup=True)

        elapsed_time = time.time() - start_time
        print_translation_summary(target_lang, translated_count, len(keys_to_translate), elapsed_time)

    def check_completeness(
        self,
        source_lang: str,
        target_langs: list[str],
        nested: Optional[bool] = None,
    ) -> list[MissingKeysReport]:
        """
        Check translation completeness without translating.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            nested: Whether to use nested structure. If None, auto-detected.
        """
        reports = []
        source_file = self.file_service.load_language_file(source_lang)
        # We don't strictly need nested here because find_missing_keys handles it,
        # but it's good for consistency if we want to override it.
        # Actually file_service.find_missing_keys needs to be updated too if we want to override.
        
        for target_lang in target_langs:
            # TODO: find_missing_keys currently doesn't accept nested override, 
            # it always uses source_file.is_nested. This is likely what we want anyway.
            report = self.file_service.find_missing_keys(source_lang, target_lang)
            reports.append(report)

        return reports
