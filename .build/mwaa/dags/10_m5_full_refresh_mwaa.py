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


# ------------------------------------------------------------------------------
# Scheduling note
# ------------------------------------------------------------------------------
DAG_START_DATE = datetime(2024, 1, 1)

DEFAULT_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "depends_on_past": False,
}

# ------------------------------------------------------------------------------
# Helper: ensure commands run from the MWAA DAGs root
# ------------------------------------------------------------------------------
# MWAA executes tasks from an Airflow working directory. We explicitly cd so that
# relative paths like "warehouse/..." resolve reliably.
MWAA_CD_ROOT = 'cd "${AIRFLOW_HOME}" || cd /usr/local/airflow || cd .'


with DAG(
    dag_id="10_m5_full_refresh_mwaa",
    description="End-to-end M5 refresh (MWAA): ingest → dq → stage → dbt silver → dbt gold",
    start_date=DAG_START_DATE,
    schedule=None,  # manual trigger for now
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
            "python -c \"from gdf.ingestion.m5_ingestion import ingest_m5_to_bronze; ingest_m5_to_bronze()\""
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
            "python -c \""
            "from gdf.quality.run_calendar_dq import run_calendar_dq; "
            "from gdf.quality.run_sell_prices_dq import run_sell_prices_dq; "
            "from gdf.quality.run_sales_train_validation_dq import run_sales_train_validation_dq; "
            "run_calendar_dq(); "
            "run_sell_prices_dq(); "
            "run_sales_train_validation_dq()"
            "\""
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
            "python -c \""
            "from warehouse.loaders.load_m5_calendar_to_staging import load_calendar_to_staging; "
            "from warehouse.loaders.load_m5_sell_prices_to_staging import load_sell_prices_to_staging; "
            "from warehouse.loaders.load_m5_sales_train_validation_to_staging import load_sales_train_validation_to_staging; "
            "load_calendar_to_staging(); "
            "load_sell_prices_to_staging(); "
            "load_sales_train_validation_to_staging()"
            "\""
        ),
        execution_timeout=timedelta(hours=2),
        pool="warehouse_pool",
    )

    # --------------------------------------------------------------------------
    # Step 4: dbt Silver build + test
    # --------------------------------------------------------------------------
    dbt_silver = BashOperator(
        task_id="dbt_silver_build_and_test",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            "dbt deps --project-dir warehouse --profiles-dir warehouse/.dbt; "
            "dbt run  --project-dir warehouse --profiles-dir warehouse/.dbt --select path:models/silver; "
            "dbt test --project-dir warehouse --profiles-dir warehouse/.dbt --select path:models/silver"
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
            "dbt deps --project-dir warehouse --profiles-dir warehouse/.dbt; "
            "dbt run  --project-dir warehouse --profiles-dir warehouse/.dbt --select path:models/gold; "
            "dbt test --project-dir warehouse --profiles-dir warehouse/.dbt --select path:models/gold"
        ),
        execution_timeout=timedelta(hours=1),
        pool="warehouse_pool",
    )

    ingest_m5 >> dq_all >> stage_all >> dbt_silver >> dbt_gold
