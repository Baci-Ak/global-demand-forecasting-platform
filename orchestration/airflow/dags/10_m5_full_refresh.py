"""
DAG: 10_m5_full_refresh

Purpose
-------
Orchestrate the existing, already-working batch pipeline end-to-end using Airflow.

What it runs (same as `make warehouse-refresh`)
-----------------------------------------------
1) Ingest M5 data to Bronze (S3/MinIO) + audit logging
2) Run DQ gates (calendar, sell_prices, sales_train_validation)
3) Load to warehouse staging tables
4) Build + test dbt Silver
5) Build + test dbt Gold

Design principles
-----------------
- Airflow orchestrates; it does NOT reimplement pipeline logic.
- Each task calls the same commands developers run locally.
- Clear task boundaries → easier debugging, retries, and future extension.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
import logging




# ------------------------------------------------------------------------------
# Scheduling note
# ------------------------------------------------------------------------------
# Airflow requires a start_date even for manually-triggered DAGs.
# We set a stable date in the past to avoid any surprises if the schedule changes
# later (and we keep catchup=False so no backfills are created).
DAG_START_DATE = datetime(2024, 1, 1)



# ------------------------------------------------------------------------------
# Failure callback (baseline)
# ------------------------------------------------------------------------------

# ...

DEFAULT_ARGS = {
    # Retry policy: transient failures (network, S3) should auto-retry.
    "retries": 2,
    "retry_delay": timedelta(minutes=5),

    # Task safety: never retry forever.
    "depends_on_past": False,
}
# ------------------------------------------------------------------------------
# DAG definition
# ------------------------------------------------------------------------------
with DAG(
    dag_id="10_m5_full_refresh",
    description="End-to-end M5 refresh: ingest → dq → stage → dbt silver → dbt gold",
    start_date=DAG_START_DATE,
    schedule=None,  # manual trigger for now
    catchup=False,
    tags=["m5", "batch", "warehouse"],
    # ----------------------------
    # Production-grade safety rails
    # ----------------------------
    default_args=DEFAULT_ARGS,

    # Prevent overlapping full refreshes (important for idempotency + cost).
    max_active_runs=1,

    # Keep concurrency conservative while hardening.
    # We can increase later once we add pools/queues properly.
    max_active_tasks=1,

    # If the DAG run exceeds this, Airflow will time it out.
    dagrun_timeout=timedelta(hours=6),
) as dag:
    # --------------------------------------------------------------------------
    # Step 1: Ingest (Bronze)
    # --------------------------------------------------------------------------
    ingest_m5 = BashOperator(
        task_id="ingest_m5_to_bronze",
        bash_command="set -euo pipefail; make ingest-m5 ingest-weather ingest-macro ingest-trends",
        cwd="/opt/project",
        execution_timeout=timedelta(hours=2),
    )

    # --------------------------------------------------------------------------
    # Step 2: Data Quality gates
    # --------------------------------------------------------------------------
    dq_all = BashOperator(
        task_id="dq_all",
        bash_command="set -euo pipefail; make dq-all",
        cwd="/opt/project",
        execution_timeout=timedelta(hours=1),
    )

    # --------------------------------------------------------------------------
    # Step 3: Stage raw data into the warehouse
    # --------------------------------------------------------------------------
    stage_all = BashOperator(
        task_id="warehouse_stage_all",
        bash_command="set -euo pipefail; make warehouse-stage-all",
        cwd="/opt/project",
        execution_timeout=timedelta(hours=2),
        pool="warehouse_pool"

    )

    # --------------------------------------------------------------------------
    # Step 4: dbt Silver build + test
    # --------------------------------------------------------------------------
    dbt_silver = BashOperator(
        task_id="dbt_silver_build_and_test",
        bash_command="set -euo pipefail; make dbt-run-silver dbt-test-silver",
        cwd="/opt/project",
        execution_timeout=timedelta(hours=1),
        pool="warehouse_pool"

    )

    # --------------------------------------------------------------------------
    # Step 5: dbt Gold build + test
    # --------------------------------------------------------------------------
    dbt_gold = BashOperator(
        task_id="dbt_gold_build_and_test",
        bash_command="set -euo pipefail; make dbt-run-gold dbt-test-gold",
        cwd="/opt/project",
        execution_timeout=timedelta(hours=1),
        pool="warehouse_pool"
    )

    # ------------------------------------------------------------------------------
    # Task dependencies (the DAG)
    # ------------------------------------------------------------------------------
    ingest_m5 >> dq_all >> stage_all >> dbt_silver >> dbt_gold
