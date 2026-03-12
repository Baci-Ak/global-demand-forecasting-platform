#!/bin/sh
set -e

# ==============================================================================
# MWAA Startup Script
# ------------------------------------------------------------------------------
# Purpose
# - Load environment-specific, non-secret runtime config from S3.
# - Fetch DSNs + other secrets from AWS Secrets Manager using IDs from the config.
# - Install the GDF application wheel from S3 (exact filename; no renaming).
# - Install dbt in an isolated virtualenv to avoid MWAA/Airflow constraints conflicts.
# - Write a local env file that Airflow tasks can source for runtime settings.
#
# Notes
# - Database migrations are NOT executed here.
# - Migrations should run as a deploy-time job (outside MWAA startup) to keep
#   environment boot deterministic.
#
# Scaling model
# - Same startup.sh for dev/prod.
# - Only gdf_runtime.conf changes per environment.
# - The S3 URI for gdf_runtime.conf is injected via env var when possible.
# ==============================================================================


# ------------------------------------------------------------------------------
# Defaults (safe fallbacks)
# ------------------------------------------------------------------------------
AWS_REGION_DEFAULT="us-east-1"
RUNTIME_CONF_PATH="/usr/local/airflow/gdf_runtime.conf"
RUNTIME_ENV_PATH="/usr/local/airflow/gdf_runtime.env"
WHEEL_TMP_PATH="/tmp"


# ------------------------------------------------------------------------------
# Load runtime config from S3
# ------------------------------------------------------------------------------
echo "[startup] Loading runtime config from S3..."

# Prefer env var injection (dev/prod), fallback keeps current behaviour.
GDF_RUNTIME_CONF_S3_URI="${GDF_RUNTIME_CONF_S3_URI:-s3://gdf-prod-airflow/airflow/startup/gdf_runtime.conf}"

aws s3 cp "${GDF_RUNTIME_CONF_S3_URI}" "${RUNTIME_CONF_PATH}"
chmod 600 "${RUNTIME_CONF_PATH}"
echo "[startup] Downloaded ${GDF_RUNTIME_CONF_S3_URI} -> ${RUNTIME_CONF_PATH}"

# shellcheck disable=SC1090
. "${RUNTIME_CONF_PATH}"

AWS_REGION="${AWS_REGION:-$AWS_REGION_DEFAULT}"


# ------------------------------------------------------------------------------
# Fetch runtime secrets from Secrets Manager
# ------------------------------------------------------------------------------
echo "[startup] Fetching runtime secrets from Secrets Manager..."

POSTGRES_DSN="$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "${POSTGRES_DSN_SECRET_ID}" \
  --query SecretString \
  --output text)"

WAREHOUSE_DSN="$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "${WAREHOUSE_DSN_SECRET_ID}" \
  --query SecretString \
  --output text)"

REDSHIFT_ADMIN_JSON="$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "${REDSHIFT_ADMIN_SECRET_ID}" \
  --query SecretString \
  --output text)"

REDSHIFT_HOST="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['host'])" "${REDSHIFT_ADMIN_JSON}")"
REDSHIFT_PORT="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['port'])" "${REDSHIFT_ADMIN_JSON}")"
REDSHIFT_USER="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['username'])" "${REDSHIFT_ADMIN_JSON}")"
REDSHIFT_PASSWORD="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['password'])" "${REDSHIFT_ADMIN_JSON}")"
REDSHIFT_DBNAME="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['dbname'])" "${REDSHIFT_ADMIN_JSON}")"
REDSHIFT_IAM_ROLE_ARN="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['copy_role_arn'])" "${REDSHIFT_ADMIN_JSON}")"

KAGGLE_SECRET_JSON="$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "${KAGGLE_SECRET_ID}" \
  --query SecretString \
  --output text)"

KAGGLE_USERNAME="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['KAGGLE_USERNAME'])" "${KAGGLE_SECRET_JSON}")"
KAGGLE_API_TOKEN="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['KAGGLE_API_TOKEN'])" "${KAGGLE_SECRET_JSON}")"
M5_COMPETITION="$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('M5_COMPETITION','m5-forecasting-accuracy'))" "${KAGGLE_SECRET_JSON}")"


MACRO_API_KEY="$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "${MACRO_SECRET_ID}" \
  --query SecretString \
  --output text)"


# ------------------------------------------------------------------------------
# Install application wheel (keep exact filename; no renaming)
# ------------------------------------------------------------------------------
echo "[startup] Installing GDF wheel from S3..."

aws s3 cp "s3://${WHEEL_S3_BUCKET}/${WHEEL_S3_KEY}" "${WHEEL_TMP_PATH}/${WHEEL_FILENAME}"
pip install "${WHEEL_TMP_PATH}/${WHEEL_FILENAME}"


# ------------------------------------------------------------------------------
# Install dbt in an isolated virtualenv (avoids MWAA/Airflow constraints conflict)
# ------------------------------------------------------------------------------
DBT_VENV="/usr/local/airflow/dbt_venv"
DBT_BIN="${DBT_VENV}/bin/dbt"


echo "[startup] Setting up dbt venv at ${DBT_VENV} ..."

# Create venv if missing
if [ ! -d "${DBT_VENV}" ]; then
  python3 -m venv "${DBT_VENV}"
fi

# Upgrade installer tooling inside the venv
"${DBT_VENV}/bin/python" -m pip install --upgrade pip setuptools wheel

# Install dbt + adapter WITH dependencies inside the venv (isolated from Airflow env) ..
"${DBT_VENV}/bin/pip" install "dbt-core==1.11.2" "dbt-redshift==1.10.0"

# Verify
"${DBT_BIN}" --version



# ------------------------------------------------------------------------------
# Write runtime env file for tasks (tasks should source this)..
# ------------------------------------------------------------------------------
cat > "${RUNTIME_ENV_PATH}" <<EOF
# Generated at MWAA startup. Source this file in tasks to load runtime settings.
export POSTGRES_DSN='${POSTGRES_DSN}'
export WAREHOUSE_DSN='${WAREHOUSE_DSN}'
export REDSHIFT_HOST='${REDSHIFT_HOST}'
export REDSHIFT_PORT='${REDSHIFT_PORT}'
export REDSHIFT_USER='${REDSHIFT_USER}'
export REDSHIFT_PASSWORD='${REDSHIFT_PASSWORD}'
export REDSHIFT_DBNAME='${REDSHIFT_DBNAME}'
export REDSHIFT_IAM_ROLE_ARN='${REDSHIFT_IAM_ROLE_ARN}'
export BRONZE_BUCKET='${BRONZE_BUCKET}'
export KAGGLE_USERNAME='${KAGGLE_USERNAME}'
export KAGGLE_API_TOKEN='${KAGGLE_API_TOKEN}'
export M5_COMPETITION='${M5_COMPETITION}'
export STAGING_SCHEMA='${STAGING_SCHEMA}'
export DBT_TARGET='${DBT_TARGET}'
export DBT_THREADS='${DBT_THREADS}'
export DBT_BIN='${DBT_BIN}'
export MAX_D_COLS='${MAX_D_COLS}'
export WEATHER_SOURCE_NAME='${WEATHER_SOURCE_NAME}'
export WEATHER_PROVIDER='${WEATHER_PROVIDER}'
export WEATHER_BASE_URL='${WEATHER_BASE_URL}'
export WEATHER_DEFAULT_HISTORICAL_DAYS='${WEATHER_DEFAULT_HISTORICAL_DAYS}'
export MACRO_SOURCE_NAME='${MACRO_SOURCE_NAME}'
export MACRO_PROVIDER='${MACRO_PROVIDER}'
export MACRO_BASE_URL='${MACRO_BASE_URL}'
export MACRO_API_KEY='${MACRO_API_KEY}'
export TRENDS_SOURCE_NAME='${TRENDS_SOURCE_NAME}'
export TRENDS_PROVIDER='${TRENDS_PROVIDER}'
export TRENDS_GEO='${TRENDS_GEO}'
EOF

# export DBT_BIN='${DBT_BIN}'

chmod 600 "${RUNTIME_ENV_PATH}"
echo "[startup] Wrote ${RUNTIME_ENV_PATH} (chmod 600)"


# ------------------------------------------------------------------------------
# Migrations
# ------------------------------------------------------------------------------
echo "[startup] Skipping Alembic migrations (handled by deploy-time migration job)"


# ------------------------------------------------------------------------------
# Sanity check imports..
# ------------------------------------------------------------------------------
python3 -c "import ingestion, quality, warehouse, database, audit_log, app_config; print('[startup] gdf imports OK')"