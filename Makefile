.PHONY: help build up down logs shell test translate-missing translate-all check languages clean

help:
	@echo "TranslateGemma CLI - Available Commands:"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build              Build Docker image"
	@echo "  make up                 Start API server"
	@echo "  make down               Stop all services"
	@echo "  make logs               View API logs"
	@echo "  make shell              Open shell in container"
	@echo ""
	@echo "Translation Commands (Docker):"
	@echo "  make translate-missing  Translate missing keys (test_messages)"
	@echo "  make translate-all      Translate all keys (test_messages)"
	@echo "  make check              Check translation completeness"
	@echo "  make languages          Show supported languages"
	@echo ""
	@echo "Development:"
	@echo "  make test               Run tests"
	@echo "  make clean              Clean up containers and cache"

# Docker operations
build:
	docker compose build

up:
	docker compose up -d api

down:
	docker compose down

logs:
	docker compose logs -f api

shell:
	docker compose run --rm cli bash

# Translation commands
translate-missing:
	./docker-run.sh translate-missing ./messages --all-languages -q 4bit

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
