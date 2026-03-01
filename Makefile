# ==============================================================================
# Global Demand Forecasting (GDF) - Makefile
# ==============================================================================
#
# Goals
# - Provide a clean, discoverable CLI for local development + AWS/MWAA operations.
# - Keep Terraform responsible for infrastructure only.
# - Keep CI/CD responsible for packaging + pushing artifacts (DAGs, plugins, startup,
#   requirements, wheel, alembic bundle) to S3.
#
# Notes
# - This Makefile is safe for local dev use.
# - CI/CD will call a subset of targets (mwaa-* targets primarily).
# - Avoid putting secrets in this file. Use env vars / AWS Secrets Manager.
# ==============================================================================


# ------------------------------------------------------------------------------
# Local env loading (developer convenience)
# - Loads .env automatically if present.
# - CI injects env vars; this only applies when .env exists locally.
# ------------------------------------------------------------------------------
ifneq (,$(wildcard .env))
include .env
export
endif


# ------------------------------------------------------------------------------
# Global defaults
# ------------------------------------------------------------------------------
AWS_REGION ?= us-east-1


# ------------------------------------------------------------------------------
# Phony targets
# ------------------------------------------------------------------------------
.PHONY: help \
	local-up local-down local-ps local-logs \
	airflow-up airflow-down airflow-ps airflow-logs airflow-reset \
	db-check db-upgrade db-downgrade db-revision db-current db-history db-schema-drop \
	aws-db-upgrade \
	s3-smoke s3-upload s3-list \
	test-mlflow test-kaggle download-kaggle ingest-m5 \
	dq-calendar dq-sell-prices dq-sales-train-validation dq-all \
	warehouse-load-calendar warehouse-load-sell-prices warehouse-load-sales-train-validation warehouse-stage-all \
	dbt-debug dbt-init-staging dbt-run-silver dbt-test-silver dbt-run-gold dbt-test-gold dbt-docs \
	warehouse-silver warehouse-gold warehouse-refresh \
	aws-azs \
	mwaa-build-plugins mwaa-upload-dags mwaa-upload-requirements mwaa-upload-plugins mwaa-upload-startup mwaa-upload-all \
	mwaa-upload-alembic \
	mwaa-build-wheel mwaa-upload-wheel \
	pkg-install \
	tunnel-mwaa-ui tunnel-rds-audit tunnel-redshift


# ==============================================================================
# Help
# ==============================================================================
help:
	@echo ""
	@echo "GDF Makefile - common commands"
	@echo "----------------------------------------------------------------"
	@echo "Local docker:"
	@echo "  make local-up                      Start local services"
	@echo "  make local-down                    Stop local services"
	@echo "  make local-ps                      Show running containers"
	@echo "  make local-logs                    Follow logs"
	@echo ""
	@echo "Local Airflow (docker-compose.airflow.yml):"
	@echo "  make airflow-up"
	@echo "  make airflow-down"
	@echo "  make airflow-ps"
	@echo "  make airflow-logs"
	@echo "  make airflow-reset                 DANGEROUS: wipes Airflow volumes"
	@echo ""
	@echo "Database / Alembic (audit DB):"
	@echo "  make db-check"
	@echo "  make db-upgrade"
	@echo "  make db-downgrade N=-1"
	@echo "  make db-revision MSG='message'"
	@echo "  make db-current"
	@echo "  make db-history"
	@echo "  make db-schema-drop                DANGEROUS: local dev only"
	@echo ""
	@echo "AWS RDS migrations (uses Secrets Manager DSN):"
	@echo "  make aws-db-upgrade POSTGRES_DSN_SECRET_ID=gdf/dev/postgres_dsn"
	@echo ""
	@echo "S3 / MinIO helpers:"
	@echo "  make s3-smoke"
	@echo "  make s3-upload FILE=... KEY=..."
	@echo "  make s3-list PREFIX=..."
	@echo ""
	@echo "Pipelines:"
	@echo "  make test-kaggle"
	@echo "  make download-kaggle"
	@echo "  make ingest-m5"
	@echo "  make dq-all"
	@echo ""
	@echo "Warehouse:"
	@echo "  make warehouse-stage-all"
	@echo "  make warehouse-silver"
	@echo "  make warehouse-gold"
	@echo "  make warehouse-refresh"
	@echo ""
	@echo "MWAA packaging + upload (CI/CD uses these):"
	@echo "  make mwaa-upload-all"
	@echo "  make mwaa-build-wheel"
	@echo "  make mwaa-upload-wheel WHEEL=dist/<file>.whl"
	@echo ""
	@echo "Private tunnels (via jumphost scripts):"
	@echo "  make tunnel-mwaa-ui"
	@echo "  make tunnel-rds-audit"
	@echo "  make tunnel-redshift"
	@echo ""


# ==============================================================================
# Local Docker (general services)
# ==============================================================================
local-up:
	docker compose up -d

local-down:
	docker compose down

local-ps:
	docker compose ps

local-logs:
	docker compose logs -f --tail=200


# ==============================================================================
# Local Airflow (docker-compose.airflow.yml)
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


# ==============================================================================
# Database / Alembic (local DSN via env/.env)
# ==============================================================================
db-check:
	python -c "from app_config.config import settings; import sqlalchemy as sa; from sqlalchemy import text; \
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
	@test -n "$(MSG)" || (echo "ERROR: set MSG='your migration message'" && exit 1)
	alembic revision --autogenerate -m "$(MSG)"

db-current:
	alembic current

db-history:
	alembic history --verbose

db-schema-drop:
	python -c "from app_config.config import settings; import sqlalchemy as sa; from sqlalchemy import text; \
e=sa.create_engine(settings.POSTGRES_DSN); \
schema=settings.AUDIT_SCHEMA; \
with e.begin() as c: c.execute(text(f'DROP SCHEMA IF EXISTS \"{schema}\" CASCADE')); \
print(f'Dropped schema: {schema}')"


# ==============================================================================
# AWS RDS: Alembic upgrade using Secrets Manager (no repo secrets)
# ==============================================================================
POSTGRES_DSN_SECRET_ID ?= gdf/dev/postgres_dsn

aws-db-upgrade:
	@echo "Running Alembic migrations using secret: $(POSTGRES_DSN_SECRET_ID) (region: $(AWS_REGION))"
	@export POSTGRES_DSN="$$(aws secretsmanager get-secret-value \
	  --region $(AWS_REGION) \
	  --secret-id $(POSTGRES_DSN_SECRET_ID) \
	  --query SecretString \
	  --output text)"; \
	alembic upgrade head


# ==============================================================================
# S3 / MinIO (dev helpers)
# ==============================================================================
s3-smoke:
	python -c "from pathlib import Path; from ingestion.s3_client import upload_file_to_bronze; \
p=Path('$(or $(FILE),local_data/m5/calendar.csv)'); \
k='$(or $(KEY),m5/raw/calendar.csv)'; \
print(upload_file_to_bronze(p, k))"

s3-upload:
	@test -n "$(FILE)" || (echo "ERROR: set FILE=path/to/file" && exit 1)
	@test -n "$(KEY)"  || (echo "ERROR: set KEY=s3/key/path" && exit 1)
	python -c "from pathlib import Path; from ingestion.s3_client import upload_file_to_bronze; \
p=Path('$(FILE)'); \
k='$(KEY)'; \
print(upload_file_to_bronze(p, k))"

s3-list:
	python -c "from ingestion.s3_client import get_s3_client; from app_config.config import settings; \
s3=get_s3_client(); \
resp=s3.list_objects_v2(Bucket=settings.BRONZE_BUCKET, Prefix='$(or $(PREFIX),)'); \
for o in resp.get('Contents', []): \
  print(o['Key'])"


# ==============================================================================
# Pipelines
# ==============================================================================
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


# ==============================================================================
# Warehouse (staging loaders + dbt)
# ==============================================================================
warehouse-load-calendar:
	python -m warehouse.loaders.load_m5_calendar_to_staging

warehouse-load-sell-prices:
	python -m warehouse.loaders.load_m5_sell_prices_to_staging

warehouse-load-sales-train-validation:
	python -m warehouse.loaders.load_m5_sales_train_validation_to_staging

warehouse-stage-all: dbt-init-staging warehouse-load-calendar warehouse-load-sell-prices warehouse-load-sales-train-validation
	@echo "✅ Staging ready (calendar, sell_prices, sales_train_validation_long)"

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

warehouse-silver: warehouse-stage-all dbt-run-silver dbt-test-silver
	@echo "✅ Silver built + tested"

warehouse-gold: warehouse-silver dbt-run-gold dbt-test-gold
	@echo "✅ Gold built + tested"

warehouse-refresh: ingest-m5 dq-all warehouse-gold
	@echo "✅ Full refresh complete (ingest -> dq -> stage -> silver -> gold)"


# ==============================================================================
# AWS helpers
# ==============================================================================
aws-azs:
	@aws ec2 describe-availability-zones \
	  --region $${AWS_REGION:-us-east-1} \
	  --query "AvailabilityZones[?State=='available'].ZoneName" \
	  --output text


# ==============================================================================
# MWAA artifacts (packaging + upload)
# - These targets only upload to S3. They do NOT modify MWAA environment settings.
# - Terraform controls which S3 object versions MWAA uses.
# ==============================================================================
MWAA_DAG_BUCKET       ?= gdf-dev-airflow
MWAA_DAG_PREFIX       ?= airflow/dags
MWAA_REQ_PREFIX       ?= airflow/requirements
MWAA_PLUGINS_PREFIX   ?= airflow/plugins
MWAA_STARTUP_PREFIX   ?= airflow/startup
MWAA_WHEEL_PREFIX     ?= airflow/packages


MWAA_PLUGINS_ZIP := .build/plugins.zip

mwaa-build-plugins:
	@mkdir -p .build
	@rm -f $(MWAA_PLUGINS_ZIP)
	@cd orchestration/airflow/plugins && zip -r ../../..//$(MWAA_PLUGINS_ZIP) . \
	  -x "*.pyc" -x "__pycache__/*" -x ".DS_Store" -x "**/.DS_Store"
	@echo "✅ Built: $(MWAA_PLUGINS_ZIP)"

mwaa-upload-dags:
	aws s3 sync orchestration/airflow/dags s3://$(MWAA_DAG_BUCKET)/$(MWAA_DAG_PREFIX) --delete \
	  --exclude "__pycache__/*" --exclude "**/__pycache__/*" --exclude "*.pyc" \
	  --exclude ".DS_Store" --exclude "**/.DS_Store"
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



# ==============================================================================
# MWAA: Upload Alembic migrations (audit DB schema)
# - MWAA tasks runs Alembic against the private RDS from inside AWS.

# ==============================================================================





# ==============================================================================
# MWAA: wheel build + upload
# ==============================================================================
mwaa-build-wheel:
	@rm -rf dist build *.egg-info
	@python -m build --wheel
	@echo "✅ Built wheel(s):"
	@ls -1 dist/*.whl

 #Usage:
#   make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
mwaa-upload-wheel:
	@test -n "$(WHEEL)" || (echo "ERROR: set WHEEL=dist/<wheel-file>.whl" && exit 1)
	@aws s3 cp $(WHEEL) s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename $(WHEEL))
	@echo "✅ Uploaded wheel -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename $(WHEEL))"


# ==============================================================================
# Developer sanity check
# ==============================================================================
pkg-install:
	python -m pip install --upgrade pip
	python -m pip install -e .
	python -c "import ingestion, quality, warehouse, warehouse.loaders, database, audit_log, app_config; print('OK: gdf package imports')"


# ==============================================================================
# AWS: SSM tunnels to private resources via jumphost scripts
# ==============================================================================
tunnel-mwaa-ui:
	@chmod +x infra/terraform/bin/tunnel_mwaa_ui.sh
	@infra/terraform/bin/tunnel_mwaa_ui.sh

tunnel-rds-audit:
	@chmod +x infra/terraform/bin/tunnel_rds_audit.sh
	@infra/terraform/bin/tunnel_rds_audit.sh

tunnel-redshift:
	@chmod +x infra/terraform/bin/tunnel_redshift.sh
	@infra/terraform/bin/tunnel_redshift.sh






# ==============================================================================
# AWS: SSM tunnels to private resources (standard interface)
# - Source of truth: SSM Parameter Store (/gdf/<env>/...)
# - Works for dev/prod by changing ENVIRONMENT=prod
# ==============================================================================

ENVIRONMENT ?= dev

.PHONY: connect-mwaa connect-postgres connect-redshift connect-mwaa-mac

connect-mwaa:
	@chmod +x infra/terraform/bin/connect_dev.sh
	@AWS_REGION=$(AWS_REGION) ENVIRONMENT=$(ENVIRONMENT) infra/terraform/bin/connect_dev.sh mwaa

connect-postgres:
	@chmod +x infra/terraform/bin/connect_dev.sh
	@AWS_REGION=$(AWS_REGION) ENVIRONMENT=$(ENVIRONMENT) infra/terraform/bin/connect_dev.sh postgres

connect-redshift:
	@chmod +x infra/terraform/bin/connect_dev.sh
	@AWS_REGION=$(AWS_REGION) ENVIRONMENT=$(ENVIRONMENT) infra/terraform/bin/connect_dev.sh redshift

# macOS convenience for MWAA: binds 443 + hosts mapping
connect-mwaa-mac:
	@chmod +x infra/terraform/bin/gdf-dev-connect-mwaa-mac.sh
	@AWS_REGION=$(AWS_REGION) ENVIRONMENT=$(ENVIRONMENT) infra/terraform/bin/gdf-dev-connect-mwaa-mac.sh



# ==============================================================================
# MWAA (CI deploy helpers)
# ==============================================================================

.PHONY: mwaa-ci-setup

mwaa-ci-setup:
	@echo "== MWAA CI setup =="
	@python -c "import sys; print('python=', sys.version)"
	@python -m pip install --upgrade pip
	@python -m pip install --upgrade build
	@echo "OK: python build tooling installed"



# ==============================================================================
# MWAA (CI deploy helpers)
# - One command CI can run to publish MWAA artifacts to S3.
# ==============================================================================

# CI metadata (GitHub Actions sets GITHUB_SHA automatically)
GIT_SHA ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "local")


.PHONY: mwaa-ci-deploy

mwaa-ci-deploy: mwaa-ci-setup
	@echo "== MWAA CI deploy =="
	@echo "Bucket:  s3://$(MWAA_DAG_BUCKET)"
	@echo "SHA:     $(GIT_SHA)"
	@echo ""
	@$(MAKE) mwaa-upload-dags
	@$(MAKE) mwaa-upload-requirements
	@$(MAKE) mwaa-upload-plugins
	@$(MAKE) mwaa-upload-startup
	@$(MAKE) mwaa-build-wheel
	@echo ""
	@WHEEL="$$(ls -1 dist/*.whl | head -n 1)"; \
	echo "Uploading wheel: $$WHEEL -> s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename "$$WHEEL")"; \
	aws s3 cp "$$WHEEL" "s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/$$(basename "$$WHEEL")"
	@echo ""
	@echo "Deployed:"
	@echo "  DAGs          s3://$(MWAA_DAG_BUCKET)/$(MWAA_DAG_PREFIX)/"
	@echo "  requirements  s3://$(MWAA_DAG_BUCKET)/$(MWAA_REQ_PREFIX)/requirements.txt"
	@echo "  plugins       s3://$(MWAA_DAG_BUCKET)/$(MWAA_PLUGINS_PREFIX)/plugins.zip"
	@echo "  startup       s3://$(MWAA_DAG_BUCKET)/$(MWAA_STARTUP_PREFIX)/"
	@echo "  wheel         s3://$(MWAA_DAG_BUCKET)/$(MWAA_WHEEL_PREFIX)/"
	@echo ""
	@echo "Done."