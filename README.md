# TranslateGemma CLI for next-intl

CLI tool for translating next-intl projects using Google's TranslateGemma model with GPU acceleration.

## Features

- **Batch Translation**: Efficient batch processing to minimize GPU overhead
- **Auto Language Discovery**: Automatically detect all language files in your project
- **Nested JSON Support**: Handle complex nested translation structures
- **Translation Validation**: Automatic validation of ICU placeholders and syntax
- **Progress Tracking**: Beautiful progress bars with Rich
- **GPU Acceleration**: TF32 optimizations for RTX 30xx/40xx GPUs
- **Completeness Checking**: Verify translation coverage across languages
- **55+ Languages**: Support for all major languages
- **Docker Support**: Run in containers with GPU acceleration

## Quick Start with Docker (Recommended)

The easiest way to run TranslateGemma is with Docker:

```bash
# Build the image
docker-compose build

# Translate missing keys (using convenience script)
./docker-run.sh translate-missing ./test_messages --all-languages

# Or use docker-compose directly
docker-compose run --rm cli translate-intl translate-missing ./test_messages -t ru
```

For detailed Docker usage, see [DOCKER.md](docs/DOCKER.md).

## Installation

### Using Docker (recommended for production)

See [DOCKER.md](docs/DOCKER.md) for complete Docker setup and usage.

### Using uv (for local development)

```bash
# Clone the repository
git clone <repository-url>
cd translategemma

# Install dependencies with uv
uv sync

# The CLI will be available as 'translate-intl'
```

### Using pip

```bash
pip install -e .
```

## Requirements

- Python 3.10+
- CUDA-compatible GPU (recommended, but CPU works too)
- ~8GB VRAM for GPU inference (RTX 3080 or better)

## Usage

### Translate Missing Keys

Translate only missing keys to target languages:

```bash
# Translate missing keys to Russian
translate-intl translate-missing ./messages -s en -t ru

# Translate to multiple languages
translate-intl translate-missing ./messages -s en -t ru -t de -t fr

# Auto-discover and translate to ALL languages
translate-intl translate-missing ./messages --all-languages
```

### Translate All Keys

Translate all keys (overwrites existing translations):

```bash
# Translate all keys to Russian and German
translate-intl translate-all ./messages -s en -t ru -t de

# Translate to all discovered languages
translate-intl translate-all ./messages --all-languages
```

### Check Translation Completeness

Check which keys are missing without translating:

```bash
# Show table of missing keys
translate-intl check ./messages --all-languages

# Output as JSON (for CI/CD)
translate-intl check ./messages --all-languages -o json

# Output as Markdown
translate-intl check ./messages --all-languages -o markdown
```

### Show Supported Languages

```bash
translate-intl languages
```

### Run via Python Module

```bash
python -m translate_intl translate-missing ./messages -t ru
```

## Advanced Options

### Batch Size

Control how many texts are translated in one batch (default: 20):

```bash
# Larger batches = faster, but more VRAM usage
translate-intl translate-missing ./messages -t ru --batch-size 50

# Smaller batches = slower, but less VRAM usage
translate-intl translate-missing ./messages -t ru --batch-size 10
```

### Max Tokens

Control maximum tokens per generation (default: 200):

```bash
translate-intl translate-missing ./messages -t ru --max-tokens 300
```

## Project Structure

```
messages/
├── en.json          # Source language
├── ru.json          # Russian translations
├── de.json          # German translations
└── fr.json          # French translations
```

### Nested JSON Support

The tool handles nested next-intl structures:

```json
{
  "auth": {
    "login": {
      "title": "Sign In",
      "form": {
        "email": "Email",
        "password": "Password"
      }
    }
  }
}
```

Internally converts to flat keys (`auth.login.title`) for translation, then restores nesting.

### ICU Message Syntax

Preserves ICU placeholders in translations:

```json
{
  "greeting": "Hello {name}",
  "items": "{count, plural, one {# item} other {# items}}"
}
```

## Performance

- **Batch Translation**: 20-50 keys processed together for efficiency
- **Context Limit**: Automatic splitting when exceeding 20,000 token limit
- **Fallback Strategy**: Individual translation on batch errors
- **GPU Memory**: ~8GB VRAM usage with bfloat16 precision

### Typical Speed

- RTX 3080: ~10-15 keys/second
- CPU: ~1-2 keys/second

## Example Output

```
$ translate-intl translate-missing ./messages --all-languages

Loading TranslateGemma model... ✓ Model loaded on cuda (NVIDIA GeForce RTX 3080, 10.0GB)

Auto-discovered languages: ru, de, fr

Checking ru...
Found 25 missing keys
⠋ Translating ru... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02
✓ Language ru: 25/25 keys translated in 2.3s (10.9 keys/sec)

Checking de...
Found 18 missing keys
⠋ Translating de... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
✓ Language de: 18/18 keys translated in 1.8s (10.0 keys/sec)

✓ Translation completed!
```

## Completeness Check Output

```
$ translate-intl check ./messages --all-languages

┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ Language ┃ Missing ┃ Total ┃ Complete ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ ru       │       0 │   100 │   100.0% │
│ de       │       5 │   100 │    95.0% │
│ fr       │      25 │   100 │    75.0% │
└──────────┴─────────┴───────┴──────────┘
```

## Supported Languages (55+)

English, German, French, Spanish, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Czech, Polish, Dutch, Swedish, Danish, Norwegian, Finnish, Turkish, Greek, Hebrew, Thai, Vietnamese, Indonesian, Malay, Romanian, Ukrainian, Bulgarian, Croatian, Slovak, Slovenian, Serbian, Estonian, Latvian, Lithuanian, Hungarian, Persian, Urdu, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Sinhala, Khmer, Lao, Burmese, Georgian, Amharic, Nepali, Swahili, Afrikaans, and more...

## Troubleshooting

### CUDA Out of Memory

Reduce batch size:

```bash
translate-intl translate-missing ./messages -t ru --batch-size 10
```

### Model Not Found

The model will be downloaded automatically on first run (~9GB). Ensure you have:
- Stable internet connection
- ~20GB free disk space (for model + cache)

### Slow Performance

- Check GPU is being used: Model will show device on load
- Reduce batch size if getting errors
- Consider using smaller max-tokens value

## Development

### Setup Development Environment

```bash
# Install dev dependencies
uv sync --extra dev

# Run linting
ruff check src/

# Run formatting
ruff format src/
```

### Project Structure

```
src/translate_intl/
├── core/
│   ├── config.py          # Configuration
│   └── translator.py      # TranslateGemma engine
├── services/
│   ├── file_service.py    # File operations
│   └── translation_service.py  # Business logic
├── models/
│   └── translation.py     # Data models
├── utils/
│   ├── json_handler.py    # JSON utilities
│   └── progress.py        # Rich output
├── cli.py                 # CLI interface
└── __main__.py            # Entry point
```

## API (Flask)

The original Flask API is still available in `api.py`:

```bash
python api.py
```

See API documentation for details.

## Documentation

For detailed guides and references, see [docs/](docs/):

- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Docker Guide](docs/DOCKER.md) - Complete Docker usage
- [Examples](docs/EXAMPLES.md) - Real-world workflows
- [Architecture](docs/PROJECT_STRUCTURE.md) - Technical details

## License

MIT

## Credits

- Model: [Google TranslateGemma](https://huggingface.co/google/translategemma-4b-it)
- CLI Framework: [Click](https://click.palletsprojects.com/)
- Terminal UI: [Rich](https://rich.readthedocs.io/)
