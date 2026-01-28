# Usage Examples

Commands below use `translate-intl`. If you are using Docker, replace
`translate-intl` with `./docker-run.sh`.

## Translate missing keys

```bash
translate-intl translate-missing ./messages --all-languages
```

## Translate all keys for specific languages

```bash
translate-intl translate-all ./messages -t de -t fr
```

## Check completeness

```bash
# Table output
translate-intl check ./messages --all-languages -o table

# JSON output
translate-intl check ./messages --all-languages -o json > report.json

# Markdown output
translate-intl check ./messages --all-languages -o markdown > TRANSLATIONS.md
```

## Glossary

Create a glossary JSON file:

```json
{
  "login": "Anmeldung",
  "password": "Passwort"
}
```

Then run:

```bash
translate-intl translate-missing ./messages -t de --glossary-path glossary.json
```

## Flat vs nested keys

If your JSON uses flat keys like `auth.login.title`, use `--flat` so keys are
not split by dots:

```bash
translate-intl translate-missing ./messages -t de --flat
```

If your JSON is nested (the default), you can force that with `--nested`:

```bash
translate-intl translate-missing ./messages -t de --nested
```

## Batch size and max tokens

```bash
# Smaller batches reduce VRAM usage
translate-intl translate-missing ./messages -t de --batch-size 10

# Increase max tokens for longer strings
translate-intl translate-missing ./messages -t de --max-tokens 300
```

## CI completeness check

```bash
set -e

translate-intl check ./messages --all-languages -o json > report.json

# Fail if any language is incomplete
jq -e '.[] | select(.completion_percentage < 100)' report.json >/dev/null && {
  echo "Incomplete translations found"
  exit 1
}
```
