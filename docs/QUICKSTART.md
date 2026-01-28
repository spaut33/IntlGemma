# Quickstart

Get a first translation running quickly. Choose Docker (recommended) or local.

## Prerequisites

- Docker Engine + Docker Compose v2 (for Docker)
- NVIDIA Container Toolkit (for GPU acceleration in Docker)
- Or Python 3.10+ with uv (for local)

## Option A: Docker (recommended)

```bash
# Build the CLI image
docker compose build cli

# Create a minimal messages directory (skip if you already have one)
mkdir -p messages
cat > messages/en.json <<'JSON'
{
  "hello": "Hello",
  "greeting": "Hello {name}"
}
JSON

echo '{}' > messages/de.json

# Translate missing keys
./docker-run.sh translate-missing ./messages -t de

# Check completeness
./docker-run.sh check ./messages -t de
```

## Option B: Local (uv)

```bash
# Install dependencies
uv sync

# Run the CLI
uv run translate-intl translate-missing ./messages -t de
uv run translate-intl check ./messages -t de
```

If your virtualenv is active (or you installed with pip), you can run:

```bash
translate-intl translate-missing ./messages -t de
```

## Notes

- The messages directory is scanned for `*.json` files. File names are language codes.
- Use `--all-languages` to translate every language file except the source.
- Use `--glossary-path glossary.json` to pin specific terms.
- Use `--flat` or `--nested` if your keys are already flat or nested.

## Next Steps

- DOCKER.md for container details
- EXAMPLES.md for workflows
- VALIDATION.md for validation rules
- PROJECT_STRUCTURE.md for repo layout
