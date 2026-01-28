"""Tests for JSON ordering utilities."""

from translate_intl.utils.json_handler import order_like_source


def test_order_like_source_nested() -> None:
    source = {"a": "x", "b": {"c": "y", "d": "z"}, "e": "w"}
    target = {"b": {"d": "D", "c": "C", "x": "X"}, "a": "A", "f": "F", "e": "E"}

    ordered = order_like_source(source, target, nested=True)

    assert list(ordered.keys()) == ["a", "b", "e", "f"]
    assert list(ordered["b"].keys()) == ["c", "d", "x"]
    assert ordered["a"] == "A"
    assert ordered["b"]["c"] == "C"
    assert ordered["b"]["d"] == "D"
    assert ordered["b"]["x"] == "X"
    assert ordered["e"] == "E"
    assert ordered["f"] == "F"


def test_order_like_source_flat() -> None:
    source = {"a": "x", "b": "y", "c": "z"}
    target = {"b": "B", "a": "A", "d": "D", "e": "E"}

    ordered = order_like_source(source, target, nested=False)

    assert list(ordered.keys()) == ["a", "b", "d", "e"]
    assert ordered["a"] == "A"
    assert ordered["b"] == "B"
    assert ordered["d"] == "D"
    assert ordered["e"] == "E"
