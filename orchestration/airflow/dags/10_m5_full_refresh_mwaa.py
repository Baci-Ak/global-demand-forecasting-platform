"""
DAG: 10_m5_full_refresh_mwaa

Purpose
-------
Orchestrate the batch pipeline end-to-end on MWAA (AWS).

What it runs (production workflow)
----------------------------------
1) Ingest M5 data to Bronze (S3) + audit logging
2) Run DQ gates (calendar, sell_prices, sales_train_validation)
3) Load to warehouse staging tables
4) Build + test dbt Silver
5) Build + test dbt Gold

Design principles
-----------------
- Airflow orchestrates; it does NOT reimplement pipeline logic.
- Tasks call the same underlying Python/dbt entrypoints used by developers.
- Clear task boundaries → easier debugging, retries, and future extension.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

import pendulum



import json
import logging
from datetime import timedelta
from typing import Any

log = logging.getLogger(__name__)


def log_task_failure(context: dict[str, Any]) -> None:
    """
    Minimal failure callback (no external integrations).
    Keeps incidents searchable in CloudWatch and easy to wire to alerting later.
    """
    ti = context.get("task_instance")
    dag = context.get("dag")
    dr = context.get("dag_run")

    payload = {
        "event": "airflow_task_failed",
        "dag_id": getattr(dag, "dag_id", None),
        "task_id": getattr(ti, "task_id", None),
        "run_id": getattr(dr, "run_id", None),
        "try_number": getattr(ti, "try_number", None),
        "state": getattr(ti, "state", None),
        "execution_date": str(context.get("execution_date")),
        "logical_date": str(context.get("logical_date")),
        "log_url": getattr(ti, "log_url", None),
    }
    log.error("TASK_FAILURE %s", json.dumps(payload, sort_keys=True))


def default_args(*, retries: int = 2) -> dict[str, Any]:
    """
    Standard default_args for production DAGs (no hardcoded email).
    Override per DAG as needed.
    """
    return {
        "owner": "data-platform",
        "retries": retries,
        "retry_delay": timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "on_failure_callback": log_task_failure,
    }








# ------------------------------------------------------------------------------
# Scheduling note
# ------------------------------------------------------------------------------
DAG_TZ = pendulum.timezone("Europe/London")
DAG_START_DATE = pendulum.datetime(2024, 1, 1, tz=DAG_TZ)

# Daily at 06:00 London time (change the cron when if you want a different time)
DAG_SCHEDULE = "0 6 * * *"




DEFAULT_ARGS = default_args(retries=2)



# DEFAULT_ARGS = {
#     "retries": 2,
#     "retry_delay": timedelta(minutes=5),
#     "depends_on_past": False,
# }

# ------------------------------------------------------------------------------
# Helper: ensure commands run from the MWAA DAGs root
# ------------------------------------------------------------------------------
# MWAA executes tasks from an Airflow working directory. We explicitly cd so that
# relative paths like "warehouse/..." resolve reliably.
#MWAA_CD_ROOT = 'cd "${AIRFLOW_HOME}" || cd /usr/local/airflow || cd .'
MWAA_CD_ROOT = (
    'cd "${AIRFLOW_HOME}" || cd /usr/local/airflow || cd .; '
    'if [ -f /usr/local/airflow/gdf_runtime.env ]; then . /usr/local/airflow/gdf_runtime.env; fi'
)


# ------------------------------------------------------------------------------
# Helpers for MWAA BashOperator commands
# ------------------------------------------------------------------------------

# Ensure dbt is available on the worker (MWAA workers can be replaced any time).
# Prefer DBT_BIN from gdf_runtime.env (written by startup.sh), but fall back to
# a known venv path and install if missing.
MWAA_ENSURE_DBT = (
    'DBT_VENV="/usr/local/airflow/dbt_venv"; '
    'if [ -n "${DBT_BIN:-}" ]; then DBT="${DBT_BIN}"; else DBT="${DBT_VENV}/bin/dbt"; fi; '
    'if [ ! -x "${DBT}" ]; then '
    '  echo "[dbt] dbt missing on worker; creating venv at ${DBT_VENV}"; '
    '  python3 -m venv "${DBT_VENV}"; '
    '  "${DBT_VENV}/bin/python" -m pip install --upgrade pip setuptools wheel; '
    '  "${DBT_VENV}/bin/pip" install "dbt-core==1.11.2" "dbt-redshift==1.10.0"; '
    '  DBT="${DBT_VENV}/bin/dbt"; '
    'fi; '
    '"${DBT}" --version; '
)

# Resolve the dbt project directory from the installed wheel.
MWAA_RESOLVE_WAREHOUSE_DIR = (
    'WAREHOUSE_DIR="$(python3 -c \'import warehouse, os; print(os.path.dirname(warehouse.__file__))\')"; '
    'echo "[dbt] WAREHOUSE_DIR=${WAREHOUSE_DIR}"; '
)

MWAA_DBT_DEPS = (
    '"${DBT}" deps --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt"; '
)





with DAG(
    dag_id="10_m5_full_refresh_mwaa",
    description="End-to-end M5 refresh (MWAA): ingest → dq → stage → dbt silver → dbt gold",
    start_date=DAG_START_DATE,
    schedule=DAG_SCHEDULE,  # manual trigger for now
    catchup=False,
    tags=["m5", "batch", "warehouse", "mwaa"],
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=6),
) as dag:
    
    # --------------------------------------------------------------------------
    # Step 1: Ingest (Bronze)
    # --------------------------------------------------------------------------
    ingest_m5 = BashOperator(
        task_id="ingest_m5_to_bronze",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            "python3 -c \"from ingestion.m5_ingestion import ingest_m5_to_bronze; ingest_m5_to_bronze()\"; "
            "python3 -c \"from ingestion.weather.weather_ingestion import ingest_weather_to_bronze; ingest_weather_to_bronze()\"; "
            "python3 -c \"from ingestion.macro.macro_ingestion import ingest_macro_to_bronze; ingest_macro_to_bronze()\"; "
            "python3 -c \"from ingestion.trends.trends_ingestion import ingest_trends_to_bronze; ingest_trends_to_bronze()\""
        ),
        execution_timeout=timedelta(hours=2),
    )

    # --------------------------------------------------------------------------
    # Step 2: Data Quality gates
    # --------------------------------------------------------------------------
    dq_all = BashOperator(
        task_id="dq_all",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            "python3 -m quality.run_calendar_dq; "
            "python3 -m quality.run_sell_prices_dq; "
            "python3 -m quality.run_sales_train_validation_dq;"
            "python3 -m quality.run_weather_daily_dq; "
            "python3 -m quality.run_macro_series_dq; "
            "python3 -m quality.run_trends_interest_over_time_dq"
        ),
        execution_timeout=timedelta(hours=1),
    )

    # --------------------------------------------------------------------------
    # Step 3: Stage raw data into the warehouse
    # --------------------------------------------------------------------------
    stage_all = BashOperator(
        task_id="warehouse_stage_all",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            f"{MWAA_ENSURE_DBT}"
            f"{MWAA_RESOLVE_WAREHOUSE_DIR}"
            # Create/init staging schema via dbt (dbt owns schema lifecycle)
            f"{MWAA_DBT_DEPS}"
            '"${DBT}" run  --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt" --select _staging_schema_init; '
            # Run the loaders
            "python3 -m warehouse.loaders.load_m5_calendar_to_staging; "
            "python3 -m warehouse.loaders.load_m5_sell_prices_to_staging; "
            "python3 -m warehouse.loaders.load_m5_sales_train_validation_to_staging;"
            "python3 -m warehouse.loaders.load_weather_daily_to_staging; "
            "python3 -m warehouse.loaders.load_macro_series_to_staging; "
            "python3 -m warehouse.loaders.load_trends_interest_over_time_to_staging"
        ),
        execution_timeout=timedelta(hours=2),
        pool="warehouse_pool",
    )
    # --------------------------------------------------------------------------
    # Step 4: dbt Silver build + test
    # --------------------------------------------------------------------------

    #make sure 'warehouse_pool' is created in the Airflow UI for warehouse_stage_all, dbt_silver, dbt_gold tasks, else, the task would never run.
    # Go to Admin → Pools,  Click + (Create), Pool: warehouse_pool, Slots: 1 (or 2 if you want dbt/staging to have room later)
    # Description: Warehouse tasks (staging + dbt)
    dbt_silver = BashOperator(
        task_id="dbt_silver_build_and_test",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            f"{MWAA_ENSURE_DBT}"
            f"{MWAA_RESOLVE_WAREHOUSE_DIR}"
            f"{MWAA_DBT_DEPS}"
            '"${DBT}" run  --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt" --select path:models/silver; '
            '"${DBT}" test --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt" --select path:models/silver'
        ),
        execution_timeout=timedelta(hours=1),
        pool="warehouse_pool",
    )

    # --------------------------------------------------------------------------
    # Step 5: dbt Gold build + test
    # --------------------------------------------------------------------------
    dbt_gold = BashOperator(
        task_id="dbt_gold_build_and_test",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            f"{MWAA_ENSURE_DBT}"
            f"{MWAA_RESOLVE_WAREHOUSE_DIR}"
            f"{MWAA_DBT_DEPS}"
            '"${DBT}" run  --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt" --select path:models/gold; '
            '"${DBT}" test --project-dir "${WAREHOUSE_DIR}" --profiles-dir "${WAREHOUSE_DIR}/.dbt" --select path:models/gold'
        ),
        execution_timeout=timedelta(hours=1),
        pool="warehouse_pool",
    )

    ingest_m5 >> dq_all >> stage_all >> dbt_silver >> dbt_gold
