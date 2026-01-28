"""Tests for translation services."""

import json

from translate_intl.services.file_service import TranslationFileService
from translate_intl.services.translation_service import TranslationService


def test_find_missing_keys_when_target_missing(tmp_path) -> None:
    messages_dir = tmp_path / "messages"
    messages_dir.mkdir()

    source_data = {"a": "x", "b": {"c": "y"}}
    (messages_dir / "en.json").write_text(json.dumps(source_data), encoding="utf-8")

    service = TranslationFileService(messages_dir)
    report = service.find_missing_keys("en", "ru")

    assert report.missing_keys == ["a", "b.c"]
    assert report.total_keys == 2


def test_load_glossary_missing_file_warns(tmp_path) -> None:
    messages_dir = tmp_path / "messages"
    messages_dir.mkdir()

    service = TranslationService(messages_dir)
    service.load_glossary(messages_dir / "missing.json")

    assert service.translator.config.glossary is None


def test_load_glossary_invalid_json_warns(tmp_path) -> None:
    messages_dir = tmp_path / "messages"
    messages_dir.mkdir()

    bad_file = messages_dir / "bad.json"
    bad_file.write_text("{", encoding="utf-8")

    service = TranslationService(messages_dir)
    service.load_glossary(bad_file)

    assert service.translator.config.glossary is None


def test_resolve_glossary_path_defaults_to_glossary_json(tmp_path, monkeypatch) -> None:
    messages_dir = tmp_path / "messages"
    messages_dir.mkdir()

    glossary_path = tmp_path / "glossary.json"
    glossary_path.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    service = TranslationService(messages_dir)
    resolved = service._resolve_glossary_path(None)

    assert resolved is not None
    assert resolved.resolve() == glossary_path.resolve()
