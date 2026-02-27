
# -----------------------------
# Local env loading
# - Loads .env automatically for local development.
# - CI/CD already injects env vars, so this only applies when .env exists.
# -----------------------------
ifneq (,$(wildcard .env))
include .env
export
endif



.PHONY: help up down ps logs \
	db-check db-schema-drop db-upgrade db-downgrade db-revision db-current db-history \
	api \
	test-mlflow test-kaggle download-kaggle ingest-m5 \
	dq-calendar dq-sell-prices dq-sales-train-validation dq-all \
	s3-smoke s3-upload s3-list \
	dbt-debug dbt-init-staging \
	warehouse-load-calendar warehouse-load-sell-prices warehouse-load-sales-train-validation warehouse-stage-all \
	dbt-run-silver dbt-test-silver dbt-run-gold dbt-test-gold dbt-docs \
	warehouse-silver warehouse-gold warehouse-refresh \
	airflow-up airflow-down airflow-ps airflow-logs airflow-reset









# -----------------------------
# Defaults / convenience
# -----------------------------
help:
	@echo "Common commands:"
	@echo "  make up                          - start local services (Postgres + MinIO + MLflow if enabled)"
	@echo "  make down                        - stop local services"
	@echo "  make ps                          - show running containers"
	@echo "  make logs                        - follow logs"
	@echo ""
	@echo "Database / Alembic (Audit DB - Postgres):"
	@echo "  make db-check                    - show which DB/host/user you are connected to"
	@echo "  make db-upgrade                  - apply migrations (alembic upgrade head)"
	@echo "  make db-downgrade N=-1           - rollback N revisions (default -1)"
	@echo "  make db-revision MSG=...         - autogenerate a new migration with message"
	@echo "  make db-current                  - show current revision"
	@echo "  make db-history                  - show migration history"
	@echo "  make db-schema-drop              - drop audit schema (DANGEROUS, local dev only)"
	@echo ""
	@echo "S3 / MinIO:"
	@echo "  make s3-smoke                    - upload a known file and print s3:// path"
	@echo "  make s3-upload FILE=... KEY=...  - upload any local file to bronze bucket"
	@echo "  make s3-list PREFIX=...          - list objects in bronze (optional PREFIX)"
	@echo ""
	@echo "API:"
	@echo "  make api                         - run FastAPI (uvicorn)"
	@echo ""
	@echo "Pipelines:"
	@echo "  make test-kaggle                 - run Kaggle API smoke test"
	@echo "  make download-kaggle             - download Kaggle dataset to local destination"
	@echo "  make ingest-m5                   - download M5 dataset + upload to Bronze + audit logging"
	@echo "  make dq-calendar                 - DQ for calendar dataset"
	@echo "  make dq-sell-prices              - DQ for sell_prices dataset"
	@echo "  make dq-sales-train-validation   - DQ for sales_train_validation dataset"
	@echo "  make dq-all                      - run all DQ gates"
	@echo ""
	@echo "Warehouse (staging loaders -> Redshift via COPY from S3):"
	@echo "  make warehouse-load-calendar                - load calendar.csv into staging.m5_calendar_raw"
	@echo "  make warehouse-load-sell-prices             - load sell_prices.csv into staging.m5_sell_prices_raw"
	@echo "  make warehouse-load-sales-train-validation  - load sales_train_validation into staging.m5_sales_train_validation_long_raw"
	@echo "  make warehouse-stage-all                    - run dbt-init-staging + all three staging loaders"
	@echo ""
	@echo "Warehouse (dbt):"
	@echo "  make dbt-debug                   - run dbt debug (from warehouse/)"
	@echo "  make dbt-init-staging            - create/init warehouse staging schema objects (dbt model)"
	@echo "  make dbt-run-silver              - build all Silver models"
	@echo "  make dbt-test-silver             - test all Silver models"
	@echo "  make dbt-run-gold                - build all Gold models"
	@echo "  make dbt-test-gold               - test all Gold models"
	@echo "  make dbt-docs                    - generate dbt documentation"
	@echo ""
	@echo "Warehouse (canonical flows):"
	@echo "  make warehouse-silver            - stage-all -> build Silver -> test Silver"
	@echo "  make warehouse-gold              - warehouse-silver -> build Gold -> test Gold"
	@echo "  make warehouse-refresh           - ingest -> dq-all -> stage-all -> silver -> gold"


	@echo ""
	@echo "Orchestration (Airflow):"
	@echo "  make airflow-up                  - start Airflow stack (dedicated metadata Postgres)"
	@echo "  make airflow-down                - stop Airflow stack"
	@echo "  make airflow-ps                  - show Airflow containers"
	@echo "  make airflow-logs                - follow Airflow logs"
	@echo "  make airflow-reset               - wipe Airflow volumes (DANGEROUS: resets metadata DB)"
	
	@echo "AWS SSM tunnels (private resources via jumphost):"
	@echo "  make tunnel-mwaa-ui                - Tunnel to MWAA private UI"
	@echo "  make tunnel-rds-audit              - Tunnel to RDS Postgres (audit DB)"
	@echo "  make tunnel-redshift               - Tunnel to Redshift endpoint"



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




# ==============================================================================
# Orchestration (Airflow) - Local-first, Production-shaped
# ------------------------------------------------------------------------------

# ==============================================================================

AIRFLOW_COMPOSE_FILE := docker-compose.airflow.yml
AIRFLOW_COMPOSE_PROJECT := gdf_airflow

airflow-up:
	docker compose -p $(AIRFLOW_COMPOSE_PROJECT) -f $(AIRFLOW_COMPOSE_FILE) up -d

airflow-down:
	docker compose -p $(AIRFLOW_COMPOSE_PROJECT) -f $(AIRFLOW_COMPOSE_FILE) down

airflow-ps:
	docker compose -p $(AIRFLOW_COMPOSE_PROJECT) -f $(AIRFLOW_COMPOSE_FILE) ps

airflow-logs:
	docker compose -p $(AIRFLOW_COMPOSE_PROJECT) -f $(AIRFLOW_COMPOSE_FILE) logs -f --tail=200

airflow-reset:
	# DANGEROUS: wipes Airflow metadata DB volume (local dev only)
	docker compose -p $(AIRFLOW_COMPOSE_PROJECT) -f $(AIRFLOW_COMPOSE_FILE) down -v





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
# MWAA / RDS: migrate audit DB (production-shaped)
# - Pulls POSTGRES_DSN from AWS Secrets Manager (same secret MWAA uses)
# - Runs Alembic upgrades against RDS (creates audit schema/tables)
# -----------------------------
POSTGRES_DSN_SECRET_ID ?= gdf/dev/postgres_dsn
AWS_REGION ?= us-east-1

.PHONY: aws-db-upgrade
aws-db-upgrade:
	@echo "Running Alembic migrations against RDS using secret: $(POSTGRES_DSN_SECRET_ID) (region: $(AWS_REGION))"
	@export POSTGRES_DSN="$$(aws secretsmanager get-secret-value \
	  --region $(AWS_REGION) \
	  --secret-id $(POSTGRES_DSN_SECRET_ID) \
	  --query SecretString \
	  --output text)"; \
	alembic upgrade head
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
# api:
# 	uvicorn database.main:app --reload


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

dq-all: dq-calendar dq-sell-prices dq-sales-train-validation
	@echo "✅ All DQ gates passed"


# -----------------------------
# Warehouse (staging loaders)
# -----------------------------
warehouse-load-calendar:
	python -m warehouse.loaders.load_m5_calendar_to_staging

warehouse-load-sell-prices:
	python -m warehouse.loaders.load_m5_sell_prices_to_staging

warehouse-load-sales-train-validation:
	python -m warehouse.loaders.load_m5_sales_train_validation_to_staging

warehouse-stage-all: dbt-init-staging warehouse-load-calendar warehouse-load-sell-prices warehouse-load-sales-train-validation
	@echo "✅ Staging ready (calendar, sell_prices, sales_train_validation_long)"


# -----------------------------
# Warehouse (dbt)
# -----------------------------
dbt-debug:
	cd warehouse && dbt debug --profiles-dir .dbt

dbt-init-staging:
	cd warehouse && dbt run --select _staging_schema_init --profiles-dir .dbt

dbt-run-silver:
	cd warehouse && dbt run --select models/silver --profiles-dir .dbt

dbt-test-silver:
	cd warehouse && dbt test --select models/silver --profiles-dir .dbt

dbt-run-gold:
	cd warehouse && dbt run --select models/gold --profiles-dir .dbt

dbt-test-gold:
	cd warehouse && dbt test --select models/gold --profiles-dir .dbt

dbt-docs:
	cd warehouse && dbt docs generate --profiles-dir .dbt


# -----------------------------
# Canonical warehouse flows (these are what CI/CD + Airflow will cal)
# -----------------------------
warehouse-silver: warehouse-stage-all dbt-run-silver dbt-test-silver
	@echo "✅ Silver built + tested"

warehouse-gold: warehouse-silver dbt-run-gold dbt-test-gold
	@echo "✅ Gold built + tested"

warehouse-refresh: ingest-m5 dq-all warehouse-gold
	@echo "✅ Full refresh complete (ingest -> dq -> stage -> silver -> gold)"




# -----------------------------
# AWS helpers
# -----------------------------
aws-azs:
	@aws ec2 describe-availability-zones \
	  --region $${AWS_REGION:-us-east-1} \
	  --query "AvailabilityZones[?State=='available'].ZoneName" \
	  --output text





# ==============================================================================
# MWAA (artifact packaging + upload)
# - These targets DO NOT modify the MWAA environment.
# - They only build/upload artifacts into the MWAA source bucket paths.
# - MWAA environment updates happen only when Terraform changes the s3_path pointers.
# ==============================================================================

#MWAA_DAG_BUCKET ?= gdf-dev-bronze

# MWAA_DAG_BUCKET ?= gdf-dev-bronze
MWAA_DAG_BUCKET ?= gdf-dev-airflow
MWAA_DAG_PREFIX ?= airflow/dags
MWAA_REQ_PREFIX ?= airflow/requirements
MWAA_PLUGINS_PREFIX ?= airflow/plugins
MWAA_STARTUP_PREFIX ?= airflow/startup

MWAA_PLUGINS_ZIP := .build/plugins.zip

.PHONY: mwaa-build-plugins mwaa-upload-dags mwaa-upload-requirements mwaa-upload-plugins mwaa-upload-startup mwaa-upload-all

mwaa-build-plugins:
	@mkdir -p .build
	@rm -f $(MWAA_PLUGINS_ZIP)
	@cd orchestration/airflow/plugins && zip -r ../../..//$(MWAA_PLUGINS_ZIP) . \
	  -x "*.pyc" -x "__pycache__/*" -x ".DS_Store" -x "**/.DS_Store"
	@echo "✅ Built: $(MWAA_PLUGINS_ZIP)"

mwaa-upload-dags:
	aws s3 sync orchestration/airflow/dags s3://$(MWAA_DAG_BUCKET)/$(MWAA_DAG_PREFIX) --delete \
	  --exclude "__pycache__/*" \
	  --exclude "**/__pycache__/*" \
	  --exclude "*.pyc" \
	  --exclude ".DS_Store" \
	  --exclude "**/.DS_Store"
	@echo "✅ Uploaded DAGs -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_DAG_PREFIX)"

mwaa-upload-requirements:
	aws s3 cp docker/airflow/requirements-mwaa.txt s3://$(MWAA_DAG_BUCKET)/$(MWAA_REQ_PREFIX)/requirements.txt
	@echo "✅ Uploaded requirements -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_REQ_PREFIX)/requirements.txt"

mwaa-upload-plugins: mwaa-build-plugins
	aws s3 cp $(MWAA_PLUGINS_ZIP) s3://$(MWAA_DAG_BUCKET)/$(MWAA_PLUGINS_PREFIX)/plugins.zip
	@echo "✅ Uploaded plugins.zip -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_PLUGINS_PREFIX)/plugins.zip"


mwaa-upload-startup:
	aws s3 cp orchestration/airflow/startup/startup.sh s3://$(MWAA_DAG_BUCKET)/$(MWAA_STARTUP_PREFIX)/startup.sh
	aws s3 cp orchestration/airflow/startup/gdf_runtime.conf s3://$(MWAA_DAG_BUCKET)/$(MWAA_STARTUP_PREFIX)/gdf_runtime.conf
	@echo "✅ Uploaded startup artifacts -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_STARTUP_PREFIX)/"


mwaa-upload-all: mwaa-upload-dags mwaa-upload-requirements mwaa-upload-plugins mwaa-upload-startup
	@echo "✅ All MWAA artifacts uploaded"



# ------------------------------------------------------------------------------
# MWAA: Build + upload application wheel
# - Builds a clean wheel from the repo root.
# - Uploads it to the MWAA source bucket under airflow/packages/.
# - Does NOT modify the MWAA environment by itself (Terraform still points to the key).
# ------------------------------------------------------------------------------

MWAA_WHEEL_PREFIX ?= airflow/packages

.PHONY: mwaa-build-wheel mwaa-upload-wheel

mwaa-build-wheel:
	@rm -rf dist build *.egg-info
	@python -m build --wheel
	@echo "✅ Built wheel(s):"
	@ls -1 dist/*.whl

# Usage:
#   make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
mwaa-upload-wheel:
	@test -n "$(WHEEL)" || (echo "ERROR: set WHEEL=dist/<wheel-file>.whl" && exit 1)
	@aws s3 cp $(WHEEL) s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename $(WHEEL))
	@echo "✅ Uploaded wheel -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename $(WHEEL))"




# ------------------------------------------------------------------------------
# MWAA: Upload Alembic migrations (audit DB schema)
# - MWAA tasks need the audit schema/tables in RDS Postgres.
# - The startup script runs `alembic upgrade head` using these files.
# ------------------------------------------------------------------------------

MWAA_ALEMBIC_PREFIX ?= airflow/startup/alembic

.PHONY: mwaa-upload-alembic

mwaa-upload-alembic:
	aws s3 cp alembic.ini s3://$(MWAA_DAG_BUCKET)/$(MWAA_ALEMBIC_PREFIX)/alembic.ini
	aws s3 sync alembic s3://$(MWAA_DAG_BUCKET)/$(MWAA_ALEMBIC_PREFIX)/alembic \
	  --delete \
	  --exclude "__pycache__/*" \
	  --exclude "*.pyc" \
	  --exclude ".DS_Store"
	@echo "✅ Uploaded Alembic -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_ALEMBIC_PREFIX)/"





.PHONY: pkg-install
pkg-install:
	python -m pip install --upgrade pip
	python -m pip install -e .
	python -c "import ingestion, quality, warehouse, warehouse.loaders, database, audit_log, app_config; print('OK: gdf package imports')"



.PHONY: mwaa-bundle
mwaa-bundle:
	@rm -rf .build/mwaa
	@mkdir -p .build/mwaa
	@rsync -a --delete \
		--exclude="__pycache__/" \
		--exclude="*.pyc" \
		--exclude="*.pyo" \
		--exclude=".DS_Store" \
		--exclude="*.egg-info/" \
		--exclude=".pytest_cache/" \
		--exclude=".ruff_cache/" \
		--exclude=".mypy_cache/" \
		--exclude=".venv*/" \
		--exclude="warehouse/target/" \
		--exclude="warehouse/logs/" \
		pyproject.toml README.md requirements-mwaa.txt \
		gdf ingestion quality warehouse database audit_log app_config \
		orchestration/airflow/dags \
		orchestration/airflow/include \
		orchestration/airflow/plugins \
		.build/mwaa/

	@cp requirements-mwaa.txt .build/mwaa/requirements.txt
	@cd .build/mwaa && zip -r ../mwaa-bundle.zip .
	@echo "Wrote .build/mwaa-bundle.zip"




# ------------------------------------------------------------------------------
# AWS: SSM tunnels to private resources via jumphost
# - Uses existing scripts in infra/terraform/bin/
# - Requires: AWS CLI + SSM permissions + .env with ENVIRONMENT and AWS_REGION
# - Each tunnel forwards a different service (MWAA UI, RDS Audit Postgres, Redshift)
# - Keep the terminal open while using the tunnel
# Usage examples:
#   make tunnel-mwaa-ui
#   make tunnel-rds-audit
#   make tunnel-redshift
# ------------------------------------------------------------------------------

.PHONY: tunnel-mwaa-ui tunnel-rds-audit tunnel-redshift

tunnel-mwaa-ui:
	@chmod +x infra/terraform/bin/tunnel_mwaa_ui.sh
	@infra/terraform/bin/tunnel_mwaa_ui.sh

tunnel-rds-audit:
	@chmod +x infra/terraform/bin/tunnel_rds_audit.sh
	@infra/terraform/bin/tunnel_rds_audit.sh

tunnel-redshift:
	@chmod +x infra/terraform/bin/tunnel_redshift.sh
	@infra/terraform/bin/tunnel_redshift.sh




# terraform apply -replace=module.mwaa.aws_mwaa_environment.this