.PHONY: help dev-up dev-down dev-logs jwt-keys migrate test lint

SERVICES := auth_service production_service maintenance_service ml_service etl_service notification_service

help:
	@echo "Targets:"
	@echo "  jwt-keys       Generate dev JWT keypair (RS256)"
	@echo "  dev-up         Start dev stack (docker compose)"
	@echo "  dev-down       Stop dev stack"
	@echo "  dev-logs       Tail logs"
	@echo "  migrate        Run alembic upgrade head on all services"
	@echo "  test           Run pytest in all services"
	@echo "  lint           Ruff + black check"

jwt-keys:
	@mkdir -p infra/jwt
	@if [ -f infra/jwt/private.pem ]; then echo "Keys already exist."; exit 0; fi
	openssl genrsa -out infra/jwt/private.pem 4096
	openssl rsa -in infra/jwt/private.pem -pubout -out infra/jwt/public.pem
	chmod 600 infra/jwt/private.pem
	@echo "JWT keys generated in infra/jwt/"

COMPOSE := docker compose -f smartbarrel.compose.yml

dev-up: jwt-keys
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(COMPOSE) up -d --build

dev-down:
	$(COMPOSE) down

dev-logs:
	$(COMPOSE) logs -f --tail=100

migrate:
	@for svc in $(SERVICES); do \
		echo "Migrating $$svc..."; \
		(cd services/$$svc && alembic upgrade head) || exit 1; \
	done

test:
	@for svc in $(SERVICES); do \
		echo "Testing $$svc..."; \
		(cd services/$$svc && PYTHONPATH=../.. pytest tests/ -q) || exit 1; \
	done

lint:
	ruff check shared services
	black --check shared services
