"""Data models for translation operations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LanguageFile:
    """Represents a language JSON file with translation keys."""

    lang_code: str
    file_path: Path
    data: dict[str, Any]

    @property
    def flat_keys(self) -> set[str]:
        """Get all keys as flat set (using dot notation)."""
        from translate_intl.utils.json_handler import flatten_dict

        return set(flatten_dict(self.data).keys())


@dataclass
class MissingKeysReport:
    """Report of missing translation keys for a language."""

    target_lang: str
    missing_keys: list[str]
    total_keys: int

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_keys == 0:
            return 100.0
        missing_count = len(self.missing_keys)
        translated_count = self.total_keys - missing_count
        return (translated_count / self.total_keys) * 100.0

    @property
    def translated_count(self) -> int:
        """Number of translated keys."""
        return self.total_keys - len(self.missing_keys)


@dataclass
class TranslationResult:
    """Result of a translation operation."""

    text: str
    source_lang: str
    target_lang: str
    processing_time: float
