"""Tests for translation validation utilities."""

import pytest

from translate_intl.utils.validators import (
    extract_icu_keywords,
    extract_placeholders,
    validate_translation,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hello {name}", {"{name}"}),
        ("{count, plural, one {# item} other {# items}}", {"{count}", "#"}),
        ("Hi {user}, you have {count} items", {"{user}", "{count}"}),
        ("Hello {{user}}", {"{{user}}"}),
        ("No placeholders here", set()),
    ],
)
def test_extract_placeholders(text: str, expected: set[str]) -> None:
    assert extract_placeholders(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("{count, plural, one {# item} other {# items}}", {"plural"}),
        ("{gender, select, male {he} female {she}}", {"select"}),
        ("Hello {name}", set()),
    ],
)
def test_extract_icu_keywords(text: str, expected: set[str]) -> None:
    assert extract_icu_keywords(text) == expected


@pytest.mark.parametrize(
    ("original", "translated", "should_be_valid"),
    [
        ("Hello {name}", "Привет {name}", True),
        ("Hello {name}", "Привет {имя}", False),
        (
            "{count, plural, one {# item} other {# items}}",
            "{count, plural, one {# элемент} other {# элементов}}",
            True,
        ),
        (
            "{count, plural, one {# item} other {# items}}",
            "{количество, множественное число, одно {# элемент}}",
            False,
        ),
        ("Simple text", "Простой текст", True),
    ],
)
def test_validate_translation(
    original: str, translated: str, should_be_valid: bool
) -> None:
    result = validate_translation(original, translated, strict=False)
    assert result.is_valid is should_be_valid


def test_validate_translation_multiline() -> None:
    original = "Line one\nLine two {name}"
    translated = "Linea uno\nLinea dos {name}"
    result = validate_translation(original, translated, strict=False)
    assert result.is_valid
