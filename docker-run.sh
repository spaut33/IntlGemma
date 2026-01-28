#!/bin/bash
# Convenience script for running translate-intl CLI in Docker

# Build image if not exists
docker compose build cli

# Run translate-intl with all arguments passed through
extra_args=()
glossary_path="$(pwd)/glossary.json"
if [ -f "$glossary_path" ]; then
    extra_args+=("-v" "$glossary_path:/app/glossary.json:ro")
fi

docker compose run --rm "${extra_args[@]}" cli translate-intl "$@"
