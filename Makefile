SHELL := /bin/bash

COMPOSE := docker compose
API_SVC := api

.DEFAULT_GOAL := help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

build: ## Build images
	$(COMPOSE) build

up: ## Start services (api + mariadb)
	$(COMPOSE) up -d --build

down: ## Stop services
	$(COMPOSE) down

logs: ## Tail logs
	$(COMPOSE) logs -f --tail=200

ps: ## Show running containers
	$(COMPOSE) ps

migrate: ## Run Alembic migrations to head
	$(COMPOSE) run --rm $(API_SVC) alembic upgrade head

revision: ## Create new Alembic revision (usage: make revision m="message")
	@if [ -z "$(m)" ]; then echo "Usage: make revision m=\"message\""; exit 1; fi
	$(COMPOSE) run --rm $(API_SVC) alembic revision --autogenerate -m "$(m)"

test: ## Run tests
	$(COMPOSE) run --rm $(API_SVC) pytest -q

lint: ## (Optional) placeholder for linting
	@echo "No linter configured. Add ruff/black if desired."

demo: ## Run a full demo flow (requires scripts/demo.sh)
	@bash scripts/demo.sh

reset: ## Reset containers (keeps DB volume)
	$(COMPOSE) down
	$(COMPOSE) up -d --build

reset-hard: ## Reset containers AND delete volumes (fresh DB)
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
