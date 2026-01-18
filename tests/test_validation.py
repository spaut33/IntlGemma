#!/usr/bin/env python3
"""Simple test script for translation validation."""

from src.translate_intl.utils.validators import (
    extract_icu_keywords,
    extract_placeholders,
    validate_translation,
)


def test_placeholder_extraction():
    """Test placeholder extraction."""
    print("=== Testing Placeholder Extraction ===\n")

    test_cases = [
        ("Hello {name}", {"name"}),
        ("{count, plural, one {# item} other {# items}}", {"count"}),
        ("Hi {user}, you have {count} items", {"user", "count"}),
        ("No placeholders here", set()),
    ]

    for text, expected in test_cases:
        result = extract_placeholders(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}'")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}\n")


def test_icu_keywords():
    """Test ICU keyword extraction."""
    print("=== Testing ICU Keyword Extraction ===\n")

    test_cases = [
        ("{count, plural, one {# item} other {# items}}", {"plural"}),
        ("{gender, select, male {he} female {she}}", {"select"}),
        ("Hello {name}", set()),
    ]

    for text, expected in test_cases:
        result = extract_icu_keywords(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}'")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}\n")


def test_validation():
    """Test translation validation."""
    print("=== Testing Translation Validation ===\n")

    test_cases = [
        # (original, translated, should_be_valid)
        ("Hello {name}", "Привет {name}", True),
        ("Hello {name}", "Привет {имя}", False),  # Translated placeholder
        (
            "{count, plural, one {# item} other {# items}}",
            "{count, plural, one {# элемент} other {# элементов}}",
            True,
        ),
        (
            "{count, plural, one {# item} other {# items}}",
            "{количество, множественное число, одно {# элемент}}",
            False,
        ),  # Lost structure
        ("Simple text", "Простой текст", True),
        ("Email", "Электронное письмо", True),  # No placeholders, valid
    ]

    for original, translated, should_be_valid in test_cases:
        result = validate_translation(original, translated, strict=False)
        is_correct = result.is_valid == should_be_valid

        status = "✅" if is_correct else "❌"
        print(f"{status} Valid={should_be_valid}")
        print(f"   Original:   {original}")
        print(f"   Translated: {translated}")
        print(f"   Result:     is_valid={result.is_valid}")

        if result.errors:
            print(f"   Errors:     {result.errors}")
        if result.warnings:
            print(f"   Warnings:   {result.warnings}")
        print()


def test_actual_translations():
    """Test actual translations from test_messages."""
    print("=== Testing Actual Translations from test_messages ===\n")

    import json
    from pathlib import Path

    en_file = Path("test_messages/en.json")
    ru_file = Path("test_messages/ru.json")

    if not en_file.exists() or not ru_file.exists():
        print("⚠ Test files not found, skipping\n")
        return

    with open(en_file) as f:
        en_data = json.load(f)

    with open(ru_file) as f:
        ru_data = json.load(f)

    from src.translate_intl.utils.json_handler import flatten_dict

    en_flat = flatten_dict(en_data)
    ru_flat = flatten_dict(ru_data)

    issues_found = 0

    for key in en_flat:
        if key not in ru_flat:
            continue

        original = en_flat[key]
        translated = ru_flat[key]

        result = validate_translation(original, translated, strict=False)

        if not result.is_valid or result.warnings:
            issues_found += 1
            print(f"{'❌' if not result.is_valid else '⚠'} Key: {key}")
            print(f"   Original:   {original}")
            print(f"   Translated: {translated}")

            if result.errors:
                print(f"   Errors:     {', '.join(result.errors)}")
            if result.warnings:
                print(f"   Warnings:   {', '.join(result.warnings)}")
            print()

    if issues_found == 0:
        print("✅ No validation issues found!\n")
    else:
        print(f"Found {issues_found} translation(s) with issues\n")


if __name__ == "__main__":
    test_placeholder_extraction()
    test_icu_keywords()
    test_validation()
    test_actual_translations()
