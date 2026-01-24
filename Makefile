.PHONY: help up down ps logs \
	db-check db-schema-drop db-upgrade db-downgrade db-revision db-current db-history \
	api \
	test-mlflow test-kaggle download-kaggle ingest-m5 \
	dq-calendar dq-sell-prices dq-sales-train-validation \
	s3-smoke s3-upload s3-list \
	warehouse-load-calendar warehouse-load-sell-prices warehouse-load-sales-train-validation \
	dbt-debug dbt-run-silver dbt-test-silver dbt-run-gold dbt-test-gold dbt-docs


# -----------------------------
# Defaults / convenience
# -----------------------------
help:
	@echo "Common commands:"
	@echo "  make up                         - start local services (Postgres + MinIO + MLflow)"
	@echo "  make down                       - stop local services"
	@echo "  make ps                         - show running containers"
	@echo "  make logs                       - follow logs"
	@echo ""
	@echo "Database / Alembic:"
	@echo "  make db-check                   - show which DB/host/user you are connected to"
	@echo "  make db-upgrade                 - apply migrations (alembic upgrade head)"
	@echo "  make db-downgrade N=-1          - rollback N revisions (default -1)"
	@echo "  make db-revision MSG=...        - autogenerate a new migration with message"
	@echo "  make db-current                 - show current revision"
	@echo "  make db-history                 - show migration history"
	@echo "  make db-schema-drop             - drop audit schema (DANGEROUS, local dev only)"
	@echo ""
	@echo "S3 / MinIO:"
	@echo "  make s3-smoke                   - upload a known file and print s3:// path"
	@echo "  make s3-upload FILE=... KEY=... - upload any local file to bronze bucket"
	@echo "  make s3-list PREFIX=...         - list objects in bronze (optional PREFIX)"
	@echo ""
	@echo "API:"
	@echo "  make api                        - run FastAPI (uvicorn)"
	@echo ""
	@echo "Pipelines:"
	@echo "  make test-mlflow                - run MLflow end-to-end smoke test"
	@echo "  make test-kaggle                - run Kaggle API smoke test"
	@echo "  make download-kaggle            - download Kaggle dataset to local destination"
	@echo "  make ingest-m5                  - download M5 dataset + upload to bronze + audit logging"
	@echo "  make dq-calendar                - data quality for the calendar dataset"
	@echo "  make dq-sell-prices             - data quality for the sell_prices dataset"
	@echo "  make dq-sales-train-validation  - data quality for sales_train_validation dataset"
	@echo ""
	@echo "Warehouse (staging loaders):"
	@echo "  make warehouse-load-calendar               - load calendar.csv into staging.m5_calendar_raw"
	@echo "  make warehouse-load-sell-prices            - load sell_prices.csv into staging.m5_sell_prices_raw"
	@echo "  make warehouse-load-sales-train-validation - load sales_train_validation.csv into staging.m5_sales_train_validation_long_raw"
	@echo ""
	@echo "Warehouse (dbt):"
	@echo "  make dbt-debug                  - run dbt debug (from warehouse/)"
	@echo "  make dbt-run-silver             - build all Silver models"
	@echo "  make dbt-test-silver            - run tests for all Silver models"
	@echo "  make dbt-run-gold               - build all Gold models"
	@echo "  make dbt-test-gold              - run tests for all Gold models"
	@echo "  make dbt-docs                  - generate dbt documentation"


# -----------------------------
# Docker
# -----------------------------
up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200


# -----------------------------
# Database / Alembic
# -----------------------------
db-check:
	python -c "from config.config import settings; import sqlalchemy as sa; from sqlalchemy import text; \
print('DSN=', settings.POSTGRES_DSN); \
e=sa.create_engine(settings.POSTGRES_DSN); \
with e.connect() as c: \
  print('connected_to=', c.execute(text('select current_database(), inet_server_addr(), inet_server_port(), current_user')).fetchone()); \
  print('audit_schema=', getattr(settings,'AUDIT_SCHEMA',None));"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade $(or $(N),-1)

db-revision:
	alembic revision --autogenerate -m "$(MSG)"

db-current:
	alembic current

db-history:
	alembic history --verbose

db-schema-drop:
	python -c "from config.config import settings; import sqlalchemy as sa; from sqlalchemy import text; \
e=sa.create_engine(settings.POSTGRES_DSN); \
schema=settings.AUDIT_SCHEMA; \
with e.begin() as c: c.execute(text(f'DROP SCHEMA IF EXISTS \"{schema}\" CASCADE')); \
print(f'Dropped schema: {schema}')"


# -----------------------------
# S3 / MinIO
# -----------------------------
s3-smoke:
	python -c "from pathlib import Path; from ingestion.s3_client import upload_file_to_bronze; \
p=Path('$(or $(FILE),local_data/m5/calendar.csv)'); \
k='$(or $(KEY),m5/raw/calendar.csv)'; \
print(upload_file_to_bronze(p, k))"

s3-upload:
	python -c "from pathlib import Path; from ingestion.s3_client import upload_file_to_bronze; \
p=Path('$(FILE)'); \
k='$(KEY)'; \
print(upload_file_to_bronze(p, k))"

s3-list:
	python -c "from ingestion.s3_client import get_s3_client; from config.config import settings; \
s3=get_s3_client(); \
resp=s3.list_objects_v2(Bucket=settings.BRONZE_BUCKET, Prefix='$(or $(PREFIX),)'); \
for o in resp.get('Contents', []): \
  print(o['Key'])"


# -----------------------------
# API
# -----------------------------
api:
	uvicorn database.main:app --reload


# -----------------------------
# Pipelines
# -----------------------------
test-mlflow:
	python training/test_mlflow.py

test-kaggle:
	python -c "from ingestion.kaggle_client import kaggle_smoke_test; kaggle_smoke_test()"

download-kaggle:
	python -c "from ingestion.kaggle_client import download_dataset; download_dataset()"

ingest-m5:
	python -c "from ingestion.m5_ingestion import ingest_m5_to_bronze; ingest_m5_to_bronze()"

dq-calendar:
	python -m quality.run_calendar_dq

dq-sell-prices:
	python -m quality.run_sell_prices_dq

dq-sales-train-validation:
	python -m quality.run_sales_train_validation_dq


# -----------------------------
# Warehouse (staging loaders)
# -----------------------------
warehouse-load-calendar:
	python -m warehouse.loaders.load_m5_calendar_to_staging

warehouse-load-sell-prices:
	python -m warehouse.loaders.load_m5_sell_prices_to_staging

warehouse-load-sales-train-validation:
	python -m warehouse.loaders.load_m5_sales_train_validation_to_staging


# -----------------------------
# Warehouse (dbt)
# -----------------------------
dbt-debug:
	cd warehouse && dbt debug

dbt-run-silver:
	cd warehouse && dbt run --select models/silver

dbt-test-silver:
	cd warehouse && dbt test --select models/silver

dbt-run-gold:
	cd warehouse && dbt run --select models/gold

dbt-test-gold:
	cd warehouse && dbt test --select models/gold

dbt-docs:
	cd warehouse && dbt docs generate
