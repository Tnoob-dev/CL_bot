COMPOSE := docker compose -f docker-compose.dev.yml

.DEFAULT_GOAL := help
.PHONY: help install run dev up down logs seed test lint fmt lock build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + dev dependencies with uv
	uv sync

run: ## Run the bot on the host (needs a reachable Postgres + data/.env)
	uv run cl-bot

dev: ## Build & start the dev stack (Postgres + bot) in the background
	$(COMPOSE) up --build -d

up: ## Start the dev stack (no rebuild)
	$(COMPOSE) up -d

down: ## Stop the dev stack
	$(COMPOSE) down

logs: ## Follow the bot logs
	$(COMPOSE) logs -f bot

seed: ## Insert sample catalog/posts so /search returns results
	$(COMPOSE) run --rm bot uv run --no-sync python scripts/seed_dev_data.py

test: ## Run the test suite
	uv run pytest

lint: ## Lint & type-check (ruff + basedpyright)
	uv run ruff check .
	uv run ruff format --check .
	uv run basedpyright

fmt: ## Auto-format the code
	uv run ruff format .
	uv run ruff check --fix .

lock: ## Refresh the uv lockfile
	uv lock

build: ## Build the production Docker image
	docker build -t cl-bot:latest .
