# Project Structure

IntlGemma is a CLI tool. There is no API service in this repository.

## Top-level layout

```
translategemma/
|-- docs/                     # Documentation
|-- messages/                 # Example messages (input/output)
|-- src/translate_intl/        # Python package
|   |-- cli.py                # Click CLI entry points
|   |-- __main__.py           # python -m translate_intl
|   |-- core/
|   |   |-- config.py         # TranslatorConfig
|   |   |-- languages.py      # Language map
|   |   `-- translator.py     # IntlGemma engine (llama.cpp)
|   |-- services/
|   |   |-- file_service.py   # Load/save JSON files
|   |   `-- translation_service.py  # Orchestration
|   |-- models/translation.py # Data models
|   `-- utils/
|       |-- json_handler.py   # Flatten/unflatten helpers
|       |-- progress.py       # Rich progress output
|       `-- validators.py     # Placeholder/ICU validation
|-- tests/                    # Test scripts
|   `-- test_validation.py
|-- Dockerfile
|-- docker-compose.yml
|-- docker-run.sh
|-- Makefile
|-- glossary.json             # Optional glossary example
`-- README.md
```

## Core flow

1. `translate-intl` (CLI) parses options in `src/translate_intl/cli.py`.
2. `TranslationService` loads messages, finds missing keys, and batches work.
3. `IntlGemmaEngine` loads the GGUF model on first use and runs inference.
4. Results are validated and written back with `.json.bak` backups.

## Messages layout

- Each language is a `*.json` file (e.g., `en.json`, `de.json`).
- Nested JSON is the default. Use `--flat` if your keys are already dotted.

## Running the CLI

- Docker: `./docker-run.sh translate-missing ./messages -t de`
- Local: `uv run translate-intl translate-missing ./messages -t de`
- Module: `python -m translate_intl translate-missing ./messages -t de`
