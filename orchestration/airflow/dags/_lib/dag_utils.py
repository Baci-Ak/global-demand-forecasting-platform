from __future__ import annotations

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