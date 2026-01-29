"""
DAG: 00_smoke_test

Purpose
-------
A minimal Airflow DAG to prove that:
1) Airflow can schedule and run tasks.
2) The repo root is mounted into the Airflow containers at /opt/project.
3) We can run simple shell commands (the same way we will run pipeline steps later).

Why this exists
---------------
Before orchestrating the real pipeline, we validate the Airflow runtime wiring:
- DAG discovery
- task execution
- logs
- filesystem mounts

This keeps debugging focused and makes onboarding easy for teammates.
"""

from __future__ import annotations

from datetime import datetime
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.log.logging_mixin import LoggingMixin



DAG_START_DATE = datetime(2024, 1, 1)

log = LoggingMixin().log

def log_task_failure(context: dict) -> None:
    ti = context.get("task_instance")
    dag_id = getattr(ti, "dag_id", "unknown_dag")
    task_id = getattr(ti, "task_id", "unknown_task")
    run_id = getattr(ti, "run_id", "unknown_run")
    log_url = getattr(ti, "log_url", "")

    log.error(
        "AIRFLOW_TASK_FAILED dag_id=%s task_id=%s run_id=%s log_url=%s",
        dag_id, task_id, run_id, log_url
    )




# ------------------------------------------------------------------------------
# DAG Definition
# ------------------------------------------------------------------------------
with DAG(
    dag_id="00_smoke_test",
    description="Smoke test: verify Airflow can run tasks and see /opt/project mount.",
    start_date=DAG_START_DATE,
    schedule=None,  # manual trigger only
    catchup=False,
    tags=["smoke", "onboarding"],
) as dag:
    # ------------------------------------------------------------------------------
    # Task: print environment + verify mount
    # ------------------------------------------------------------------------------
    verify_mount_and_context = BashOperator(
        task_id="verify_mount_and_context",
        bash_command="""
        set -euo pipefail
        echo "=== Who am I? ==="
        whoami
        echo ""

        echo "=== Working directory ==="
        pwd
        echo ""

        echo "=== List /opt/project (repo mount) ==="
        ls -la /opt/project | head -n 50
        echo ""

        echo "=== Confirm repo files exist ==="
        test -f /opt/project/Makefile && echo "Found Makefile ✅"
        test -d /opt/project/orchestration && echo "Found orchestration/ ✅"
        echo ""

        echo "Smoke test complete ✅"
        """,
    )