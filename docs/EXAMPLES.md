# Usage Examples

This document provides practical examples for common translation workflows.

## Basic Translation Workflows

### 1. First-Time Setup

```bash
# Build Docker image
docker-compose build

# Verify installation
./docker-run.sh --help
```

### 2. Translate New Project

```bash
# Create messages directory structure
mkdir -p messages
echo '{"hello": "Hello", "world": "World"}' > messages/en.json
echo '{}' > messages/ru.json
echo '{}' > messages/de.json

# Translate to all languages
./docker-run.sh translate-missing ./messages --all-languages

# Verify results
cat messages/ru.json
cat messages/de.json
```

### 3. Update Existing Translations

```bash
# Add new keys to en.json
echo '{"new_feature": {"title": "New Feature"}}' >> messages/en.json

# Translate only missing keys
./docker-run.sh translate-missing ./messages --all-languages

# Check completeness
./docker-run.sh check ./messages --all-languages
```

## Advanced Workflows

### Selective Language Translation

```bash
# Translate to specific languages only
./docker-run.sh translate-missing ./messages -t ru -t de

# Skip certain languages
./docker-run.sh translate-missing ./messages -t fr -t es -t it
```

### Performance Optimization

```bash
# Small files: Use larger batch size
./docker-run.sh translate-missing ./messages --all-languages --batch-size 50

# Large files: Use smaller batch size to avoid OOM
./docker-run.sh translate-missing ./messages --all-languages --batch-size 10

# Very long translations: Increase max tokens
./docker-run.sh translate-missing ./messages -t ru --max-tokens 300
```

### CI/CD Integration

```bash
#!/bin/bash
# ci-translate-check.sh

set -e

# Build image
docker-compose build cli

# Check translation completeness
OUTPUT=$(./docker-run.sh check ./messages --all-languages -o json)

# Parse JSON and check if all languages are 100% complete
echo "$OUTPUT" | jq -e '.[] | select(.completion_percentage < 100)' && {
    echo "ERROR: Incomplete translations found"
    echo "$OUTPUT" | jq '.'
    exit 1
}

echo "SUCCESS: All translations complete"
```

### Batch Processing Multiple Projects

```bash
#!/bin/bash
# translate-all-projects.sh

PROJECTS=(
    "project1/messages"
    "project2/messages"
    "project3/messages"
)

for project in "${PROJECTS[@]}"; do
    echo "Translating $project..."
    ./docker-run.sh translate-missing "./$project" --all-languages
    ./docker-run.sh check "./$project" --all-languages -o table
done
```

## Real-World Examples

### Example 1: E-commerce Website

```json
// messages/en.json
{
  "nav": {
    "home": "Home",
    "products": "Products",
    "cart": "Shopping Cart",
    "checkout": "Checkout"
  },
  "product": {
    "add_to_cart": "Add to Cart",
    "price": "Price: ${price}",
    "availability": "{stock, plural, =0 {Out of stock} one {# item left} other {# items in stock}}"
  },
  "checkout": {
    "title": "Complete Your Order",
    "shipping_address": "Shipping Address",
    "payment_method": "Payment Method",
    "total": "Total: ${amount}"
  }
}
```

```bash
# Translate to multiple languages
./docker-run.sh translate-missing ./messages -t ru -t de -t fr -t es -t zh -t ja

# Verify ICU placeholders preserved
./docker-run.sh check ./messages --all-languages -o table
```

### Example 2: SaaS Dashboard

```json
// messages/en.json
{
  "dashboard": {
    "welcome": "Welcome back, {username}!",
    "stats": {
      "users": "{count, plural, one {# user} other {# users}}",
      "revenue": "Revenue: ${amount}",
      "growth": "Growth: {percentage}%"
    }
  },
  "settings": {
    "profile": "Profile Settings",
    "security": "Security & Privacy",
    "billing": "Billing Information"
  },
  "notifications": {
    "success": "Changes saved successfully",
    "error": "An error occurred: {message}",
    "warning": "Please review your settings"
  }
}
```

```bash
# Translate with larger batch size (many short strings)
./docker-run.sh translate-missing ./messages --all-languages --batch-size 40
```

### Example 3: Documentation Website

```json
// messages/en.json
{
  "docs": {
    "getting_started": {
      "title": "Getting Started",
      "intro": "This guide will help you set up your first project in minutes.",
      "step1": "Step 1: Install the dependencies",
      "step2": "Step 2: Configure your environment",
      "step3": "Step 3: Run your first build"
    },
    "api": {
      "reference": "API Reference",
      "authentication": "Authentication",
      "endpoints": "Available Endpoints"
    }
  }
}
```

```bash
# Translate documentation to major languages
./docker-run.sh translate-missing ./messages -t es -t fr -t de -t pt -t zh -t ja

# Generate markdown report for documentation
./docker-run.sh check ./messages --all-languages -o markdown > TRANSLATIONS_STATUS.md
```

## Output Format Examples

### Table Output

```bash
./docker-run.sh check ./messages --all-languages -o table
```

```
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ Language ┃ Missing ┃ Total ┃ Complete ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ ru       │       0 │   100 │   100.0% │
│ de       │       5 │   100 │    95.0% │
│ fr       │      25 │   100 │    75.0% │
└──────────┴─────────┴───────┴──────────┘
```

### JSON Output

```bash
./docker-run.sh check ./messages --all-languages -o json
```

```json
[
  {
    "language": "ru",
    "missing_keys": [],
    "total_keys": 100,
    "completion_percentage": 100.0
  },
  {
    "language": "de",
    "missing_keys": ["auth.login.title", "settings.profile", ...],
    "total_keys": 100,
    "completion_percentage": 95.0
  }
]
```

### Markdown Output

```bash
./docker-run.sh check ./messages --all-languages -o markdown
```

```markdown
| Language | Missing | Total | Complete |
|----------|---------|-------|----------|
| ru       | 0       | 100   | 100.0%   |
| de       | 5       | 100   | 95.0%    |
| fr       | 25      | 100   | 75.0%    |
```

## Troubleshooting Examples

### Memory Issues

```bash
# If you get CUDA OOM errors
./docker-run.sh translate-missing ./messages -t ru --batch-size 5

# Monitor GPU memory
docker-compose run --rm cli bash -c "nvidia-smi"
```

### Slow Performance

```bash
# Verify GPU is being used
docker-compose run --rm cli bash -c "nvidia-smi"

# Check if model is downloaded
ls -lh ~/.cache/huggingface/hub/

# Increase batch size for better performance
./docker-run.sh translate-missing ./messages -t ru --batch-size 40
```

### Validation Examples

```bash
# Check specific languages
./docker-run.sh check ./messages -t ru -t de -o table

# Export missing keys for manual review
./docker-run.sh check ./messages --all-languages -o json | jq '.[] | select(.completion_percentage < 100)'

# Generate report for stakeholders
./docker-run.sh check ./messages --all-languages -o markdown > TRANSLATION_REPORT.md
```

## API Examples

### Start API Server

```bash
# Start in background
docker-compose up -d api

# Check health
curl http://localhost:5000/health
```

### Translate via API

```bash
# Single translation
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_lang": "en",
    "target_lang": "ru"
  }'

# Response
{
  "translation": "Привет, мир!",
  "source_lang": "en",
  "target_lang": "ru",
  "model": "translategemma-4b",
  "processing_time_seconds": 0.8
}
```

### Batch Translation Script

```python
# batch_translate_api.py
import requests
import json

API_URL = "http://localhost:5000/translate"

texts = [
    "Hello",
    "World",
    "Good morning"
]

for text in texts:
    response = requests.post(API_URL, json={
        "text": text,
        "source_lang": "en",
        "target_lang": "ru"
    })

    result = response.json()
    print(f"{text} -> {result['translation']}")
```

## Automation Scripts

### Nightly Translation Update

```bash
#!/bin/bash
# cron-translate.sh
# Add to crontab: 0 2 * * * /path/to/cron-translate.sh

cd /path/to/project

# Pull latest translations
git pull

# Translate missing keys
./docker-run.sh translate-missing ./messages --all-languages

# Commit if changes
if git diff --quiet messages/; then
    echo "No translation updates"
else
    git add messages/
    git commit -m "chore: auto-update translations"
    git push
fi
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if en.json was modified
if git diff --cached --name-only | grep -q "messages/en.json"; then
    echo "Source language file modified, checking translations..."

    # Run completeness check
    ./docker-run.sh check ./messages --all-languages -o json > /tmp/translation-check.json

    # Warn if translations are incomplete
    if cat /tmp/translation-check.json | jq -e '.[] | select(.completion_percentage < 100)' > /dev/null; then
        echo "WARNING: Some translations are incomplete"
        cat /tmp/translation-check.json | jq '.[] | select(.completion_percentage < 100)'

        read -p "Continue commit? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi
```

## Tips and Best Practices

### 1. Start Small

```bash
# Test with a small subset first
./docker-run.sh translate-missing ./messages -t ru

# Then expand to all languages
./docker-run.sh translate-missing ./messages --all-languages
```

### 2. Regular Checks

```bash
# Add to your workflow
make check  # or ./docker-run.sh check ./messages --all-languages
```

### 3. Backup Before Translating

```bash
# Backup is created automatically (.json.bak)
# But you can also manually backup
cp -r messages messages.backup
./docker-run.sh translate-all ./messages --all-languages
```

### 4. Use Version Control

```bash
# Always commit before translating
git add messages/
git commit -m "feat: add new translation keys"

# Translate
./docker-run.sh translate-missing ./messages --all-languages

# Review changes
git diff messages/

# Commit translations
git add messages/
git commit -m "chore: update translations"
```
