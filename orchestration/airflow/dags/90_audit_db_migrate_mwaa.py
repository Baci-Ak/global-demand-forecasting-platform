"""
DAG: 90_audit_db_migrate_mwaa

Purpose
-------
Manual, on-demand Alembic migrations for the Audit DB (private RDS Postgres).

Why this exists
---------------
- GitHub-hosted runners cannot reach private RDS endpoints (VPC-only).
- MWAA runs inside the VPC, so it can safely run migrations without opening RDS.

Design principles
-----------------
- No secrets in DAG code.
- Runtime settings are sourced from /usr/local/airflow/gdf_runtime.env (written by startup.sh).
- Alembic bundle location is configured via ALEMBIC_S3_URI in gdf_runtime.conf.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

# ------------------------------------------------------------------------------
# Scheduling
# ------------------------------------------------------------------------------
DAG_TZ = pendulum.timezone("Europe/London")
DAG_START_DATE = pendulum.datetime(2024, 1, 1, tz=DAG_TZ)

# ------------------------------------------------------------------------------
# Common shell prologue
# - Ensures it runs from a stable directory.
# - Sources runtime env written at MWAA startup (DSNs, schema, S3 URIs, etc).
# ------------------------------------------------------------------------------
MWAA_CD_ROOT = (
    'cd "${AIRFLOW_HOME}" || cd /usr/local/airflow || cd .; '
    'if [ -f /usr/local/airflow/gdf_runtime.env ]; then . /usr/local/airflow/gdf_runtime.env; fi'
)

# ------------------------------------------------------------------------------
# Alembic command
# ------------------------------------------------------------------------------
# Notes:
# - Uses ALEMBIC_S3_URI from runtime env (e.g., s3://<bucket>/airflow/startup/alembic)
# - Uses POSTGRES_DSN + AUDIT_SCHEMA from runtime env (written by startup.sh)
# ------------------------------------------------------------------------------
ALEMBIC_UPGRADE_HEAD = (
    "set -euo pipefail; "
    f"{MWAA_CD_ROOT}; "
    'test -n "${ALEMBIC_S3_URI:-}" || (echo "[alembic][ERROR] ALEMBIC_S3_URI not set" && exit 1); '
    'test -n "${POSTGRES_DSN:-}" || (echo "[alembic][ERROR] POSTGRES_DSN not set" && exit 1); '
    'test -n "${AUDIT_SCHEMA:-}" || (echo "[alembic][ERROR] AUDIT_SCHEMA not set" && exit 1); '
    'WORKDIR="/tmp/gdf_alembic"; rm -rf "${WORKDIR}"; mkdir -p "${WORKDIR}"; '
    'echo "[alembic] Downloading bundle from ${ALEMBIC_S3_URI}"; '
    'aws s3 cp "${ALEMBIC_S3_URI}/alembic.ini" "${WORKDIR}/alembic.ini"; '
    'aws s3 sync "${ALEMBIC_S3_URI}/alembic" "${WORKDIR}/alembic"; '
    'cd "${WORKDIR}"; '
    'echo "[alembic] Running upgrade head (schema=${AUDIT_SCHEMA})"; '
    "alembic -c alembic.ini upgrade head; "
    'echo "[alembic] Done."'
)

with DAG(
    dag_id="90_audit_db_migrate_mwaa",
    description="Manual Alembic migrations for Audit DB (runs inside MWAA).",
    start_date=DAG_START_DATE,
    schedule=None,  # manual only
    catchup=False,
    tags=["gdf", "db", "alembic", "manual"],
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
) as dag:
    alembic_upgrade_head = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command=ALEMBIC_UPGRADE_HEAD,
        execution_timeout=timedelta(minutes=20),
    )