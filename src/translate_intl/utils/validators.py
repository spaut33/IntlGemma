"""Translation validation utilities."""

import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of translation validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


def extract_placeholders(text: str) -> set[str]:
    """
    Extract all {placeholder} names from text.

    Handles both simple {name} and complex {count, plural, ...} placeholders.

    Args:
        text: Text with placeholders

    Returns:
        Set of placeholder names (without braces)

    Examples:
        "Hello {name}" -> {"name"}
        "{count, plural, one {# item}}" -> {"count"}
        "Hi {user}, you have {count} items" -> {"user", "count"}
    """
    # Match {placeholder} or {placeholder, ...}
    # Capture only the first word before comma or closing brace
    pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, text)
    return set(matches)


def extract_icu_keywords(text: str) -> set[str]:
    """
    Extract ICU MessageFormat keywords from text.

    Args:
        text: Text with ICU syntax

    Returns:
        Set of ICU keywords found

    Examples:
        "{count, plural, one {# item}}" -> {"plural"}
        "{gender, select, male {he} female {she}}" -> {"select"}
    """
    # ICU keywords appear after first comma in {placeholder, keyword, ...}
    keywords = {"plural", "select", "selectordinal"}
    found = set()

    for keyword in keywords:
        if re.search(rf"\{{\w+,\s*{keyword}\s*,", text):
            found.add(keyword)

    return found


def validate_placeholders(original: str, translated: str) -> ValidationResult:
    """
    Validate that translation preserves all placeholders.

    Checks:
    1. All placeholders from original exist in translation
    2. No extra placeholders added in translation
    3. Placeholder names are unchanged

    Args:
        original: Original text
        translated: Translated text

    Returns:
        ValidationResult with errors if placeholders don't match
    """
    errors = []
    warnings = []

    orig_placeholders = extract_placeholders(original)
    trans_placeholders = extract_placeholders(translated)

    # Check for missing placeholders
    missing = orig_placeholders - trans_placeholders
    if missing:
        errors.append(
            f"Missing placeholders in translation: {{{', '.join(sorted(missing))}}}"
        )

    # Check for extra placeholders (likely translated)
    extra = trans_placeholders - orig_placeholders
    if extra:
        errors.append(
            f"Extra/translated placeholders found: {{{', '.join(sorted(extra))}}}"
        )

    # Check ICU keywords
    orig_keywords = extract_icu_keywords(original)
    trans_keywords = extract_icu_keywords(translated)

    missing_keywords = orig_keywords - trans_keywords
    if missing_keywords:
        errors.append(f"ICU keywords lost: {', '.join(sorted(missing_keywords))}")

    # Warn if translation looks like it has translated ICU content
    if orig_keywords and not trans_keywords:
        warnings.append("ICU syntax appears to be completely translated/broken")

    is_valid = len(errors) == 0

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_translation(original: str, translated: str, strict: bool = True) -> ValidationResult:
    """
    Comprehensive translation validation.

    Args:
        original: Original text
        translated: Translated text
        strict: If True, treat warnings as errors

    Returns:
        ValidationResult with all validation issues
    """
    result = validate_placeholders(original, translated)

    # Additional checks
    errors = list(result.errors)
    warnings = list(result.warnings)

    # Check for empty translation
    if not translated.strip():
        errors.append("Translation is empty")

    # Check for unchanged translation (possible translation failure)
    if original.strip() == translated.strip() and len(original) > 3:
        warnings.append("Translation unchanged (possible failure)")

    # Check for suspiciously long translation (>3x original)
    if len(translated) > len(original) * 3 and len(original) > 10:
        warnings.append(
            f"Translation is {len(translated) / len(original):.1f}x longer than original"
        )

    # In strict mode, treat warnings as errors
    if strict and warnings:
        errors.extend(warnings)
        warnings = []

    is_valid = len(errors) == 0

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def format_validation_error(
    key: str, original: str, translated: str, result: ValidationResult
) -> str:
    """
    Format validation error for display.

    Args:
        key: Translation key
        original: Original text
        translated: Translated text
        result: ValidationResult

    Returns:
        Formatted error message
    """
    lines = [f"Validation failed for '{key}':"]
    lines.append(f"  Original:   {original}")
    lines.append(f"  Translated: {translated}")

    if result.errors:
        lines.append("  Errors:")
        for error in result.errors:
            lines.append(f"    - {error}")

    if result.warnings:
        lines.append("  Warnings:")
        for warning in result.warnings:
            lines.append(f"    - {warning}")

    return "\n".join(lines)
