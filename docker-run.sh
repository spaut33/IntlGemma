#!/bin/bash
# Convenience script for running translate-intl CLI in Docker

# Build image if not exists
docker compose build cli

# Run translate-intl with all arguments passed through
docker compose run --rm cli translate-intl "$@"
