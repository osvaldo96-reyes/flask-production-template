.DEFAULT_GOAL := help
.PHONY: help up down clean logs ps test lint e2e

help: ## Muestra esta ayuda
	@grep -E '^[a-z0-9-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

up: ## Levanta el stack y espera a que esté healthy
	docker compose up -d --build --wait

down: ## Detiene el stack (conserva los datos)
	docker compose down

clean: ## Detiene el stack y borra el volumen de la base de datos
	docker compose down -v

logs: ## Logs de todos los servicios
	docker compose logs -f --tail=50

ps: ## Estado de los servicios
	docker compose ps

test: ## Tests unitarios con cobertura
	pytest --cov=app --cov-report=term-missing --cov-fail-under=85

lint: ## ruff + hadolint + shellcheck
	ruff check . && ruff format --check .
	hadolint Dockerfile
	shellcheck scripts/*.sh

e2e: ## Pruebas de punta a punta contra el stack levantado
	./scripts/e2e.sh
