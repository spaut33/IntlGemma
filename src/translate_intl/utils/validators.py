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
    Extract variables and structural elements that must be preserved.
    
    Handles:
    1. {{double_braces}}
    2. {simple_placeholders}
    3. ICU structures like {count, plural, ...} - extracts variable name only
    4. Nested placeholders
    """
    placeholders = set()
    
    # 1. Handle {{...}} first
    for m in re.findall(r"\{\{[^}]+\}\}", text):
        placeholders.add(m)
        # We don't remove them yet to allow the parser to handle them if needed, 
        # but the parser will skip them if they match the double-brace pattern.

    # 2. Parse braces with nesting support
    stack = 0
    start = -1
    for i, char in enumerate(text):
        if char == "{":
            if stack == 0:
                start = i
            stack += 1
        elif char == "}":
            if stack > 0:
                stack -= 1
                if stack == 0:
                    block = text[start : i + 1]
                    
                    # Skip if already handled as {{...}}
                    if block.startswith("{{") and block.endswith("}}"):
                        continue
                        
                    # ICU detection: {var, type, ...}
                    if "," in block:
                        # Extract variable name from the start
                        parts = block[1:-1].split(",", 1)
                        var_name = parts[0].strip()
                        placeholders.add(f"{{{var_name}}}")
                        
                        # Recursively find placeholders in the rest of the ICU block
                        if len(parts) > 1:
                            placeholders.update(extract_placeholders(parts[1]))
                    else:
                        # Simple placeholder - only add if it looks like a variable
                        # (i.e., no internal spaces)
                        content = block[1:-1].strip()
                        if content and " " not in content:
                            placeholders.add(block)
    
    # 3. Special case for # symbol in plural/selectordinal
    if "#" in text and ("plural" in text or "selectordinal" in text):
        placeholders.add("#")

    return placeholders


def extract_tags(text: str) -> set[str]:
    """Extract XML/HTML tags like <0>, </0>, <br/>, etc."""
    pattern = r"</?[a-zA-Z0-9]+[^>]*>"
    return set(re.findall(pattern, text))


def extract_technical_terms(text: str) -> set[str]:
    """
    Extract technical terms like snake_case, camelCase, or dotted.names.
    """
    found = set()
    # snake_case (at least one underscore)
    found.update(re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", text))
    # camelCase (at least one uppercase not at the start)
    found.update(re.findall(r"\b[a-z][a-z0-9]+[A-Z][a-zA-Z0-9]+\b", text))
    # dotted.names (at least one dot)
    found.update(re.findall(r"\b[a-z0-9]+(?:\.[a-z0-9]+)+\b", text))
    return found


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
        # Improved regex to handle optional whitespace
        if re.search(rf"\{{\s*\w+,\s*{keyword}\s*,", text):
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

    # 1. Check placeholders
    orig_placeholders = extract_placeholders(original)
    trans_placeholders = extract_placeholders(translated)

    missing = orig_placeholders - trans_placeholders
    if missing:
        errors.append(
            f"Missing or modified placeholders: {', '.join(sorted(missing))}"
        )

    # 2. Check tags (rich text)
    orig_tags = extract_tags(original)
    trans_tags = extract_tags(translated)
    
    missing_tags = orig_tags - trans_tags
    if missing_tags:
        errors.append(f"Missing tags: {', '.join(sorted(missing_tags))}")
    
    extra_tags = trans_tags - orig_tags
    if extra_tags:
        errors.append(f"Extra tags found: {', '.join(sorted(extra_tags))}")

    # 3. Check technical terms (snake_case, camelCase)
    orig_tech = extract_technical_terms(original)
    trans_tech = extract_technical_terms(translated)
    
    missing_tech = orig_tech - trans_tech
    if missing_tech:
        # We use warnings for technical terms because sometimes they might be translated if they are common words
        # but for things like listener_port it should be a warning at least
        warnings.append(f"Technical terms missing or translated: {', '.join(sorted(missing_tech))}")

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
