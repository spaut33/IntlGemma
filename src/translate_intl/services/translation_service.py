"""Translation service orchestrating file operations and model inference."""

import json
import time
from pathlib import Path

from rich.console import Console

from translate_intl.core.config import TranslatorConfig
from translate_intl.core.translator import TranslateGemmaEngine
from translate_intl.models.translation import LanguageFile, MissingKeysReport
from translate_intl.services.file_service import TranslationFileService
from translate_intl.utils.json_handler import flatten_dict, order_like_source
from translate_intl.utils.progress import create_translation_progress, print_translation_summary
from translate_intl.utils.validators import (
    format_validation_error,
    validate_translation,
)

console = Console()


class TranslationService:
    """High-level service for translating next-intl projects."""

    def __init__(
        self, messages_dir: Path, translator_config: TranslatorConfig | None = None
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
        if not glossary_path.exists():
            console.print(f"[yellow]Warning: Glossary not found: {glossary_path}[/yellow]")
            return

        try:
            content = glossary_path.read_text(encoding="utf-8")
        except OSError as e:
            console.print(f"[yellow]Warning: Unable to read glossary {glossary_path}: {e}[/yellow]")
            return

        try:
            glossary = json.loads(content)
        except json.JSONDecodeError as e:
            console.print(f"[yellow]Warning: Invalid glossary JSON in {glossary_path}: {e}[/yellow]")
            return

        if not isinstance(glossary, dict):
            console.print(
                f"[yellow]Warning: Glossary must be a JSON object: {glossary_path}[/yellow]"
            )
            return

        self.translator.config.glossary = glossary
        console.print(f"[green]✓[/green] Loaded glossary with {len(glossary)} terms")

    def _resolve_nested(self, nested: bool | None, source_file: LanguageFile) -> bool:
        if nested is None:
            return source_file.is_nested

        if nested != source_file.is_nested:
            flag = "--nested" if nested else "--flat"
            structure = "nested" if source_file.is_nested else "flat"
            console.print(
                f"[yellow]Warning: {flag} ignored; source file is {structure}[/yellow]"
            )
            return source_file.is_nested

        return nested

    def _resolve_glossary_path(self, glossary_path: Path | None) -> Path | None:
        if glossary_path is not None:
            return glossary_path

        default_path = Path("glossary.json")
        if default_path.is_file():
            return default_path

        return None

    def translate_all(
        self,
        source_lang: str,
        target_langs: list[str],
        max_tokens: int = 200,
        batch_size: int = 20,
        nested: bool | None = None,
        glossary_path: Path | None = None,
    ) -> None:
        """
        Translate all keys to target languages.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            max_tokens: Maximum tokens per generation
            batch_size: Number of texts to translate in one batch
            nested: Preferred structure. If None, auto-detected; conflicts are ignored.
            glossary_path: Path to glossary JSON file (optional). Defaults to ./glossary.json if present.
        """
        resolved_glossary_path = self._resolve_glossary_path(glossary_path)
        if resolved_glossary_path:
            self.load_glossary(resolved_glossary_path)

        # Load model once for all languages
        self.translator.load_model(show_progress=True)

        source_file = self.file_service.load_language_file(source_lang)
        
        is_nested = self._resolve_nested(nested, source_file)
        
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
        nested: bool | None = None,
        glossary_path: Path | None = None,
    ) -> None:
        """
        Translate only missing keys to target languages.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            max_tokens: Maximum tokens per generation
            batch_size: Number of texts to translate in one batch
            nested: Preferred structure. If None, auto-detected; conflicts are ignored.
            glossary_path: Path to glossary JSON file (optional). Defaults to ./glossary.json if present.
        """
        resolved_glossary_path = self._resolve_glossary_path(glossary_path)
        if resolved_glossary_path:
            self.load_glossary(resolved_glossary_path)

        # Load model once for all languages
        self.translator.load_model(show_progress=True)

        source_file = self.file_service.load_language_file(source_lang)
        
        is_nested = self._resolve_nested(nested, source_file)

        for target_lang in target_langs:
            console.print(f"\n[bold cyan]Checking {target_lang}...[/bold cyan]")

            # Find missing keys
            report = self.file_service.find_missing_keys(
                source_lang, target_lang, nested=is_nested
            )

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

        target_path = self.file_service.messages_dir / f"{target_lang}.json"
        if target_path.exists():
            target_file = self.file_service.load_language_file(target_lang)
            target_data = target_file.data
        else:
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

                    if len(translations) != len(batch_texts):
                        raise ValueError(
                            "Translation batch size mismatch: "
                            f"expected {len(batch_texts)}, got {len(translations)}"
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
        target_file.data = order_like_source(source_data, target_data, nested=nested)
        self.file_service.save_language_file(target_file, backup=True)

        elapsed_time = time.time() - start_time
        print_translation_summary(target_lang, translated_count, len(keys_to_translate), elapsed_time)

    def check_completeness(
        self,
        source_lang: str,
        target_langs: list[str],
        nested: bool | None = None,
    ) -> list[MissingKeysReport]:
        """
        Check translation completeness without translating.

        Args:
            source_lang: Source language code
            target_langs: List of target language codes
            nested: Preferred structure. If None, auto-detected; conflicts are ignored.
        """
        reports = []
        source_file = self.file_service.load_language_file(source_lang)
        is_nested = self._resolve_nested(nested, source_file)

        for target_lang in target_langs:
            report = self.file_service.find_missing_keys(
                source_lang, target_lang, nested=is_nested
            )
            reports.append(report)

        return reports
