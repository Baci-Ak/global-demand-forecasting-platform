.PHONY: help up down ps logs test-mlflow test-kaggle ingest-m5 dq-calendar

help:
	@echo "Common commands:"
	@echo "  make up           - start local services (Postgres + MinIO + MLflow)"
	@echo "  make down         - stop local services"
	@echo "  make ps           - show running containers"
	@echo "  make logs         - follow logs"
	@echo "  make test-mlflow  - run MLflow end-to-end smoke test"
	@echo "  make test-kaggle  - run Kaggle API smoke test"
	@echo "  make ingest-m5    - download M5 dataset + upload to bronze + audit logging"
	@echo "  make dq-calendar   - Data quality for the calendar dataset"

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

test-kaggle:
	python -c "from ingestion.kaggle_client import kaggle_smoke_test; kaggle_smoke_test()"

ingest-m5:
	python -c "from ingestion.m5_ingestion import ingest_m5_to_bronze; ingest_m5_to_bronze()"

dq-calendar:
	python quality/run_calendar_dq.py
