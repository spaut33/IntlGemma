# Project Structure

Complete overview of the TranslateGemma CLI project structure.

## Directory Layout

```
translategemma/
├── src/
│   └── translate_intl/          # Main package
│       ├── __init__.py           # Package initialization
│       ├── __main__.py           # Entry point for python -m translate_intl
│       ├── cli.py                # CLI commands (Click)
│       │
│       ├── core/                 # Core translation engine
│       │   ├── __init__.py
│       │   ├── config.py         # TranslatorConfig dataclass
│       │   └── translator.py    # TranslateGemmaEngine with batch processing
│       │
│       ├── services/             # Business logic
│       │   ├── __init__.py
│       │   ├── file_service.py  # File I/O and language discovery
│       │   └── translation_service.py  # Translation orchestration
│       │
│       ├── models/               # Data models
│       │   ├── __init__.py
│       │   └── translation.py   # LanguageFile, MissingKeysReport, etc.
│       │
│       └── utils/                # Utilities
│           ├── __init__.py
│           ├── json_handler.py  # Nested JSON handling
│           └── progress.py      # Rich progress bars and formatting
│
├── test_messages/                # Test translation files
│   ├── en.json                   # Source language
│   ├── ru.json                   # Russian translations
│   ├── de.json                   # German translations
│   └── fr.json                   # French translations
│
├── api.py                        # Legacy Flask API server
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Locked dependencies (uv)
│
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker services (API + CLI)
├── docker-run.sh                 # Convenience script for CLI
├── .dockerignore                 # Docker build exclusions
├── .env.example                  # Environment variables template
│
├── Makefile                      # Convenience commands
│
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
├── DOCKER.md                     # Docker usage guide
├── EXAMPLES.md                   # Real-world examples
└── PROJECT_STRUCTURE.md          # This file

```

## Core Components

### 1. Translation Engine (`core/translator.py`)

**TranslateGemmaEngine** - Main translation engine

- **Lazy loading**: Model loads on first use
- **Batch translation**: Groups texts for efficiency
- **Context limit handling**: Automatic splitting for large batches
- **GPU optimization**: TF32, bfloat16, inference mode
- **Fallback strategy**: Individual translation on batch errors

Key methods:
- `load_model()` - Load TranslateGemma model
- `translate()` - Translate single text
- `translate_batch()` - Batch translate (main optimization)
- `get_device_info()` - GPU/CPU diagnostics

### 2. File Service (`services/file_service.py`)

**TranslationFileService** - Manages translation files

- **Auto-discovery**: Finds all `*.json` language files
- **Nested JSON**: Handles complex next-intl structures
- **Missing keys**: Compares source and target languages
- **Backup**: Creates `.json.bak` before overwriting

Key methods:
- `discover_languages()` - Auto-find language files
- `load_language_file()` - Load and parse JSON
- `save_language_file()` - Save with backup
- `find_missing_keys()` - Compare source vs target

### 3. Translation Service (`services/translation_service.py`)

**TranslationService** - Orchestrates translations

- **Batch processing**: Splits keys into batches
- **Progress tracking**: Rich progress bars
- **Error handling**: Continues on batch errors
- **Statistics**: Speed, time, success rate

Key methods:
- `translate_all()` - Translate all keys
- `translate_missing()` - Translate only missing keys
- `check_completeness()` - Report without translating

### 4. JSON Utilities (`utils/json_handler.py`)

Functions for nested JSON handling:

- `flatten_dict()` - Convert nested to flat keys
- `unflatten_dict()` - Restore nested structure
- `get_nested_value()` - Get value by flat key
- `set_nested_value()` - Set value by flat key (immutable)
- `is_icu_message()` - Detect ICU placeholders
- `extract_icu_placeholders()` - Extract placeholder names

### 5. CLI Interface (`cli.py`)

**Click-based commands:**

- `translate-all` - Translate all keys
- `translate-missing` - Translate missing keys only
- `check` - Check completeness
- `languages` - Show supported languages

Features:
- Auto language discovery (`--all-languages`)
- Batch size control (`--batch-size`)
- Output formats (table, JSON, markdown)
- Progress bars with Rich

## Data Models

### LanguageFile

```python
@dataclass
class LanguageFile:
    lang_code: str          # e.g., "en", "ru"
    file_path: Path         # Path to JSON file
    data: dict[str, Any]    # Nested JSON data

    @property
    def flat_keys(self) -> set[str]:
        # All keys as flat set
```

### MissingKeysReport

```python
@dataclass
class MissingKeysReport:
    target_lang: str         # e.g., "ru"
    missing_keys: list[str]  # List of missing flat keys
    total_keys: int          # Total keys in source

    @property
    def completion_percentage(self) -> float:
        # Percentage of translated keys
```

### TranslatorConfig

```python
@dataclass
class TranslatorConfig:
    model_id: str = "google/translategemma-4b-it"
    device: str = "auto"
    torch_dtype: torch.dtype = torch.bfloat16
    max_new_tokens: int = 200
    temperature: float = 0.1
    enable_tf32: bool = True
    cache_dir: Optional[str] = None
```

## Docker Components

### Dockerfile

Multi-stage build with:
- CUDA 13.0 runtime
- Python 3.12
- uv package manager
- All dependencies pre-installed

### docker-compose.yml

Two services:
1. **api** - Flask API server (port 5000)
2. **cli** - Interactive CLI (profile: cli)

Shared configuration:
- GPU access (all NVIDIA GPUs)
- HuggingFace cache mount
- 2GB shared memory

### docker-run.sh

Convenience script:
```bash
./docker-run.sh translate-missing ./messages -t ru
# Equivalent to:
docker-compose run --rm cli translate-intl translate-missing ./messages -t ru
```

## Workflow

### Translation Pipeline

```
1. CLI Command
   ↓
2. TranslationService
   ├── Load source language file
   ├── Discover/validate target languages
   └── For each target language:
       ↓
3. Find missing keys
   ├── Load target file (or create)
   └── Compare with source
       ↓
4. Batch translation
   ├── Split keys into batches (size: 20)
   ├── For each batch:
   │   ├── translate_batch()
   │   │   ├── Combine texts into single prompt
   │   │   ├── Check context limit
   │   │   ├── Generate translation
   │   │   └── Parse numbered results
   │   └── Update target data
   └── Save with backup
       ↓
5. Display statistics
   └── Keys translated, time, speed
```

### Batch Translation Flow

```
Input: ["Hello", "World", "Sign In"]
   ↓
Combine into prompt:
   "Translate the following texts:
    1. Hello
    2. World
    3. Sign In"
   ↓
TranslateGemma model
   ↓
Output:
   "1. Привет
    2. Мир
    3. Войти"
   ↓
Parse numbered results
   ↓
Return: ["Привет", "Мир", "Войти"]
```

### Nested JSON Handling

```
Input JSON:
{
  "auth": {
    "login": {
      "title": "Sign In"
    }
  }
}
   ↓
flatten_dict()
   ↓
{
  "auth.login.title": "Sign In"
}
   ↓
Translate keys
   ↓
{
  "auth.login.title": "Войти"
}
   ↓
unflatten_dict()
   ↓
Output JSON:
{
  "auth": {
    "login": {
      "title": "Войти"
    }
  }
}
```

## Dependencies

### Production

- **click** (>=8.1.7) - CLI framework
- **rich** (>=13.7.0) - Terminal formatting
- **torch** (>=2.1.0) - PyTorch for model
- **transformers** (>=4.38.0) - HuggingFace Transformers
- **accelerate** (>=0.26.0) - Model optimization

### Development

- **ruff** (>=0.1.13) - Linting and formatting
- **pytest** (>=7.4.4) - Testing framework

### API (Optional)

- **flask** (>=3.1.2) - Web framework
- **pillow** (>=12.1.0) - Image support

## Configuration

### Environment Variables

See `.env.example`:
- `HF_HOME` - HuggingFace cache directory
- `HF_TOKEN` - HuggingFace API token (optional)
- `MODEL_ID` - Model identifier
- `ENABLE_TF32` - GPU optimization flag

### pyproject.toml

Key sections:
- `[project]` - Metadata
- `[project.dependencies]` - Required packages
- `[project.scripts]` - Entry points
- `[tool.ruff]` - Linting configuration
- `[build-system]` - Build backend (hatchling)

## Entry Points

### CLI Entry Point

`pyproject.toml`:
```toml
[project.scripts]
translate-intl = "translate_intl.cli:cli"
```

Usage:
```bash
translate-intl --help
```

### Python Module

`__main__.py`:
```python
from translate_intl.cli import cli

if __name__ == "__main__":
    cli()
```

Usage:
```bash
python -m translate_intl --help
```

## Testing

### Test Files

`test_messages/` contains sample translations:
- `en.json` - Source with nested structure and ICU placeholders
- `ru.json`, `de.json`, `fr.json` - Empty target files

### Running Tests

```bash
# With Docker
make test

# Native (with uv)
uv run pytest
```

## Extension Points

### Adding New Commands

Add to `cli.py`:
```python
@cli.command()
@click.argument('messages_dir', type=click.Path(exists=True))
def my_command(messages_dir):
    """My custom command."""
    # Implementation
```

### Custom Translators

Extend `TranslateGemmaEngine`:
```python
class MyCustomEngine(TranslateGemmaEngine):
    def translate(self, text, source_lang, target_lang):
        # Custom logic
        return super().translate(text, source_lang, target_lang)
```

### Additional File Formats

Extend `TranslationFileService`:
```python
class YAMLFileService(TranslationFileService):
    def load_language_file(self, lang_code):
        # Load YAML instead of JSON
```

## Performance Characteristics

### Model Loading
- First load: ~30-60 seconds
- Memory: ~9GB disk, ~8GB VRAM

### Translation Speed
- Single text: 0.5-1.0s (includes overhead)
- Batch (20 texts): 1.5-2.5s (0.1s per text)
- Throughput: ~10-15 keys/second (RTX 3080)

### Memory Usage
- Model: ~8GB VRAM
- Batch size 20: +0.5GB VRAM
- Batch size 50: +1.0GB VRAM

### Disk Usage
- Model cache: ~9GB
- Dependencies: ~5GB
- Docker image: ~15GB

## Maintenance

### Updating Dependencies

```bash
# Update all
uv sync --upgrade

# Update specific package
uv add click@latest
```

### Linting and Formatting

```bash
# Check
ruff check src/

# Format
ruff format src/

# Fix auto-fixable issues
ruff check src/ --fix
```

### Building Docker Image

```bash
# Build
docker-compose build

# Force rebuild
docker-compose build --no-cache
```

## Future Enhancements

Potential improvements:
- [ ] Support for YAML, TOML formats
- [ ] Translation memory/glossary
- [ ] Parallel translation of multiple languages
- [ ] Web UI for translation management
- [ ] Integration with CI/CD platforms
- [ ] Translation quality scoring
- [ ] Custom model fine-tuning support
