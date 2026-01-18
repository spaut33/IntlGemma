"""Service for managing translation files."""

import json
import shutil
from pathlib import Path
from typing import Any

from translate_intl.models.translation import LanguageFile, MissingKeysReport
from translate_intl.utils.json_handler import flatten_dict, get_nested_value, set_nested_value


class TranslationFileService:
    """Service for reading/writing next-intl translation files."""

    def __init__(self, messages_dir: Path):
        """
        Initialize file service.

        Args:
            messages_dir: Path to messages directory containing language JSON files
        """
        self.messages_dir = Path(messages_dir)
        if not self.messages_dir.exists():
            raise FileNotFoundError(f"Messages directory not found: {messages_dir}")

    def discover_languages(self, exclude: list[str] | None = None) -> list[str]:
        """
        Auto-discover available language codes from JSON files.

        Args:
            exclude: List of language codes to exclude (e.g., source language)

        Returns:
            List of language codes (file names without .json)

        Example:
            For files: en.json, ru.json, de.json
            Returns: ['en', 'ru', 'de']
        """
        exclude = exclude or []
        json_files = self.messages_dir.glob("*.json")
        lang_codes = [f.stem for f in json_files if f.stem not in exclude]
        return sorted(lang_codes)

    def load_language_file(self, lang_code: str) -> LanguageFile:
        """
        Load language JSON file.

        Args:
            lang_code: Language code (e.g., 'en', 'ru')

        Returns:
            LanguageFile object

        Raises:
            FileNotFoundError: If language file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        file_path = self.messages_dir / f"{lang_code}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Language file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return LanguageFile(lang_code=lang_code, file_path=file_path, data=data)

    def save_language_file(self, lang_file: LanguageFile, backup: bool = True) -> None:
        """
        Save language file with optional backup.

        Args:
            lang_file: LanguageFile to save
            backup: Create .json.bak backup before overwriting
        """
        if backup and lang_file.file_path.exists():
            backup_path = lang_file.file_path.with_suffix(".json.bak")
            shutil.copy2(lang_file.file_path, backup_path)

        with open(lang_file.file_path, "w", encoding="utf-8") as f:
            json.dump(lang_file.data, f, ensure_ascii=False, indent=2)
            f.write("\n")  # Add trailing newline

    def create_language_file(self, lang_code: str, initial_data: dict | None = None) -> LanguageFile:
        """
        Create new language file.

        Args:
            lang_code: Language code
            initial_data: Initial data (empty dict if None)

        Returns:
            LanguageFile object
        """
        file_path = self.messages_dir / f"{lang_code}.json"
        data = initial_data or {}

        lang_file = LanguageFile(lang_code=lang_code, file_path=file_path, data=data)
        self.save_language_file(lang_file, backup=False)

        return lang_file

    def find_missing_keys(self, source_lang: str, target_lang: str) -> MissingKeysReport:
        """
        Find missing translation keys in target language.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            MissingKeysReport with details

        Raises:
            FileNotFoundError: If source or target file not found
        """
        source_file = self.load_language_file(source_lang)
        source_data_flat = flatten_dict(source_file.data)
        
        try:
            target_file = self.load_language_file(target_lang)
            target_data_flat = flatten_dict(target_file.data)
        except FileNotFoundError:
            # Target file doesn't exist - all keys are missing
            source_keys = sorted(source_data_flat.keys())
            return MissingKeysReport(
                target_lang=target_lang, missing_keys=source_keys, total_keys=len(source_keys)
            )

        missing = []
        for key, source_value in source_data_flat.items():
            target_value = target_data_flat.get(key)
            # Key is missing OR its value is identical to source (placeholder/untranslated)
            if key not in target_data_flat or target_value == source_value:
                missing.append(key)

        return MissingKeysReport(
            target_lang=target_lang, 
            missing_keys=sorted(missing), 
            total_keys=len(source_data_flat)
        )

    def get_value_by_flat_key(self, data: dict[str, Any], flat_key: str) -> Any:
        """
        Get value from nested dict using flat key.

        Args:
            data: Nested dictionary
            flat_key: Dot-separated key (e.g., 'auth.login.title')

        Returns:
            Value at the specified path

        Raises:
            KeyError: If key not found
        """
        return get_nested_value(data, flat_key)

    def set_value_by_flat_key(
        self, data: dict[str, Any], flat_key: str, value: Any
    ) -> dict[str, Any]:
        """
        Set value in nested dict using flat key (immutable).

        Args:
            data: Nested dictionary
            flat_key: Dot-separated key
            value: Value to set

        Returns:
            New dictionary with updated value
        """
        return set_nested_value(data, flat_key, value)
