"""Utilities for working with nested JSON structures in next-intl format."""

import re
from copy import deepcopy
from typing import Any


def flatten_dict(data: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, str]:
    """
    Convert nested dict to flat dict with dotted keys.

    Example:
        {'auth': {'login': {'title': 'Login'}}} -> {'auth.login.title': 'Login'}

    Args:
        data: Nested dictionary to flatten
        parent_key: Parent key for recursion (internal use)
        sep: Separator for nested keys (default: '.')

    Returns:
        Flattened dictionary with dotted keys
    """
    items: list[tuple[str, str]] = []

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, str(value)))

    return dict(items)


def unflatten_dict(flat_data: dict[str, str], sep: str = ".") -> dict[str, Any]:
    """
    Convert flat dict with dotted keys to nested dict.

    Example:
        {'auth.login.title': 'Login'} -> {'auth': {'login': {'title': 'Login'}}}

    Args:
        flat_data: Flat dictionary with dotted keys
        sep: Separator used in keys (default: '.')

    Returns:
        Nested dictionary structure
    """
    result: dict[str, Any] = {}

    for flat_key, value in flat_data.items():
        parts = flat_key.split(sep)
        current = result

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def get_nested_value(data: dict[str, Any], flat_key: str, sep: str = ".") -> Any:
    """
    Get value from nested dict using flat key.

    Args:
        data: Nested dictionary
        flat_key: Dotted key (e.g., 'auth.login.title')
        sep: Separator used in key (default: '.')

    Returns:
        Value at the specified path

    Raises:
        KeyError: If key path doesn't exist
    """
    parts = flat_key.split(sep)
    current = data

    for part in parts:
        current = current[part]

    return current


def set_nested_value(
    data: dict[str, Any], flat_key: str, value: Any, sep: str = "."
) -> dict[str, Any]:
    """
    Set value in nested dict using flat key (immutable - returns new dict).

    Args:
        data: Nested dictionary
        flat_key: Dotted key (e.g., 'auth.login.title')
        value: Value to set
        sep: Separator used in key (default: '.')

    Returns:
        New dictionary with updated value
    """
    result = deepcopy(data)
    parts = flat_key.split(sep)
    current = result

    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value
    return result


def is_icu_message(text: str) -> bool:
    """
    Check if text contains ICU message syntax.

    Examples:
        'Hello {name}' -> True
        '{count, plural, one {# item} other {# items}}' -> True
        'Simple text' -> False

    Args:
        text: Text to check

    Returns:
        True if text contains ICU placeholders
    """
    return bool(re.search(r"\{[^}]+\}", text))


def extract_icu_placeholders(text: str) -> list[str]:
    """
    Extract ICU placeholders from text.

    Example:
        'Hello {name}, you have {count} items' -> ['name', 'count']

    Args:
        text: Text containing ICU placeholders

    Returns:
        List of placeholder names
    """
    matches = re.findall(r"\{([^},]+)(?:[,}])", text)
    return matches
