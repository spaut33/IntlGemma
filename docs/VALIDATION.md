# Translation Validation

TranslateGemma validates each translated string before writing it to disk.
This helps preserve placeholders and ICU syntax.

## What is checked

- Placeholders: `{name}`, `{{name}}`, and ICU blocks like `{count, plural, ...}`
- Rich text tags: `<0>`, `</0>`, `<br/>`
- Technical identifiers: `snake_case`, `camelCase`, `dotted.names`
- ICU keywords: `plural`, `select`, `selectordinal`
- Empty translations, unchanged text, and overly long outputs

## Severity and behavior

- Errors: missing or extra placeholders/tags, missing ICU keywords, empty output.
  The CLI logs the error and keeps the original text as a fallback.
- Warnings: missing technical identifiers, unchanged text, or very long output.
  The CLI logs the warning and keeps the translation.

The CLI uses `strict=False`, so warnings do not block updates.

## Examples

```text
Original:  "Hello {name}"
Valid:     "Hallo {name}"
Error:     "Hallo {Name}"        (placeholder changed)
```

```text
Original:  "<0>Save</0>"
Error:     "<0>Save</1>"         (tag mismatch)
```

```text
Original:  "{count, plural, one {# item} other {# items}}"
Error:     "{count, one {# item} other {# items}}"  (keyword lost)
```

## Running validation tests

Local:

```bash
uv run pytest tests/test_validation.py
```

Docker:

```bash
docker compose run --rm cli uv run pytest tests/test_validation.py
```

You can also run the script directly to print sample output:

```bash
python tests/test_validation.py
```
