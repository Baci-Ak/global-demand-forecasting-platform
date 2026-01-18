.PHONY: help up down ps logs test-mlflow

help:
	@echo "Common commands:"
	@echo "  make up     - start local services (Postgres + MinIO + MLflow)"
	@echo "  make down   - stop local services"
	@echo "  make ps     - show running containers"
	@echo "  make logs   - follow logs"
	@echo "  make test-mlflow  - run MLflow end-to-end smoke test"


up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

test-mlflow:
	python training/test_mlflow.py
