.PHONY: help build shell test translate-missing translate-all check languages clean

help:
	@echo "TranslateGemma CLI - Available Commands:"
	@echo ""
	@echo "Docker CLI Commands:"
	@echo "  make build              Build Docker image"
	@echo "  make shell              Open shell in container"
	@echo "  make test               Run tests"
	@echo "  make clean              Clean up containers and cache"
	@echo ""
	@echo "Translation Commands (Docker):"
	@echo "  make translate-missing  Translate missing keys (messages)"
	@echo "  make translate-all      Translate all keys (messages)"
	@echo "  make check              Check translation completeness"
	@echo "  make languages          Show supported languages"

# Docker operations
build:
	docker compose build cli

shell:
	docker compose run --rm cli bash

# Translation commands
translate-missing:
	./docker-run.sh translate-missing ./messages --all-languages

translate-all:
	./docker-run.sh translate-all ./messages --all-languages

check:
	./docker-run.sh check ./messages --all-languages -o table

languages:
	./docker-run.sh languages

# Development
test:
	docker compose run --rm cli uv run pytest

clean:
	docker compose down -v
	docker system prune -f
