"""
DAG: 23_export_forecast_app_snapshot

Purpose
-------
Export the latest forecast application snapshot from the warehouse-backed
forecast outputs to the public S3 snapshot location.

What it does
------------
1) Load the MWAA runtime environment written by startup.sh
2) Run the forecast snapshot export module inside MWAA
3) Publish the latest and history snapshot artifacts to S3

Design principles
-----------------
- MWAA orchestrates snapshot publishing after forecast generation
- snapshot serving stays decoupled from direct warehouse access in the public app
- the public Streamlit app reads only from published snapshot artifacts
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

log = logging.getLogger(__name__)


def log_task_failure(context: dict[str, Any]) -> None:
    """
    Minimal failure callback for searchable CloudWatch logging.
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


def default_args(*, retries: int = 1) -> dict[str, Any]:
    """
    Standard production-safe default args.
    """
    return {
        "owner": "forecast-application",
        "retries": retries,
        "retry_delay": timedelta(minutes=10),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "on_failure_callback": log_task_failure,
    }


DAG_TZ = pendulum.timezone("Europe/London")
DAG_START_DATE = pendulum.datetime(2024, 1, 1, tz=DAG_TZ)
DAG_SCHEDULE = "30 4 * * *"
DEFAULT_ARGS = default_args(retries=1)

MWAA_CD_ROOT = (
    'cd "${AIRFLOW_HOME}" || cd /usr/local/airflow || cd .; '
    'if [ -f /usr/local/airflow/gdf_runtime.env ]; then . /usr/local/airflow/gdf_runtime.env; fi'
)


with DAG(
    dag_id="23_export_forecast_app_snapshot",
    description="Export the latest forecast application snapshot to S3",
    start_date=DAG_START_DATE,
    schedule=DAG_SCHEDULE,
    catchup=False,
    tags=["forecast-app", "snapshot", "mwaa", "s3"],
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=2),
) as dag:

    export_forecast_app_snapshot = BashOperator(
        task_id="export_forecast_app_snapshot",
        bash_command=(
            "set -euo pipefail; "
            f"{MWAA_CD_ROOT}; "
            "python3 -m forecast_app.snapshot_export.export_latest_snapshot"
        ),
        execution_timeout=timedelta(hours=2),
    )