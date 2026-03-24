"""
DAG: 21_train_lightgbm_ecs

Purpose
-------
Run production LightGBM training on ECS, orchestrated by MWAA.

What it does
------------
1) Resolve ECS runtime coordinates from SSM Parameter Store at task runtime
2) Run the shared ML runtime container on ECS/Fargate
3) Override the container command to run: train-lightgbm
4) Wait for completion and surface failures in Airflow / CloudWatch

Design principles
-----------------
- MWAA orchestrates; ECS performs the heavy compute work
- No hardcoded infrastructure coordinates inside the DAG body
- No live AWS API calls at DAG import time
- Runtime coordinates are resolved only at task execution time
- Keep the DAG focused on a single operational responsibility
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import boto3
import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Failure callback
# ------------------------------------------------------------------------------

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
        "owner": "ml-platform",
        "retries": retries,
        "retry_delay": timedelta(minutes=10),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "on_failure_callback": log_task_failure,
    }


# ------------------------------------------------------------------------------
# Time / schedule
# ------------------------------------------------------------------------------

DAG_TZ = pendulum.timezone("Europe/London")
DAG_START_DATE = pendulum.datetime(2024, 1, 1, tz=DAG_TZ)
DAG_SCHEDULE = "0 2 * * 1"
DEFAULT_ARGS = default_args(retries=1)


# ------------------------------------------------------------------------------
# Runtime discovery contract
# ------------------------------------------------------------------------------

AWS_REGION = "us-east-1"
SSM_PREFIX = "/gdf/prod"

ECS_CLUSTER_NAME_PARAM = f"{SSM_PREFIX}/ecs/ml_runtime_cluster_name"
MLFLOW_TRACKING_URI_PARAM = f"{SSM_PREFIX}/mlflow/tracking_uri"
TASK_DEFINITION_PARAM = f"{SSM_PREFIX}/ecs/ml_runtime_task_definition_family"
SUBNETS_PARAM = f"{SSM_PREFIX}/ecs/ml_runtime_private_subnet_ids"
SECURITY_GROUP_PARAM = f"{SSM_PREFIX}/ecs/ml_runtime_security_group_id"


with DAG(
    dag_id="21_train_lightgbm_ecs",
    description="Production LightGBM training on ECS",
    start_date=DAG_START_DATE,
    schedule=DAG_SCHEDULE,
    catchup=False,
    tags=["ml", "training", "ecs", "lightgbm"],
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    max_active_tasks=2,
    dagrun_timeout=timedelta(hours=8),
) as dag:

    @task(task_id="resolve_ecs_runtime_config")
    def resolve_ecs_runtime_config() -> dict[str, Any]:
        """
        Resolve required ECS runtime coordinates from SSM.

        Runs at task execution time, not DAG parse time.
        """
        ssm = boto3.client("ssm", region_name=AWS_REGION)

        required_names = [
            ECS_CLUSTER_NAME_PARAM,
            MLFLOW_TRACKING_URI_PARAM,
            TASK_DEFINITION_PARAM,
            SUBNETS_PARAM,
            SECURITY_GROUP_PARAM,
        ]

        response = ssm.get_parameters(
            Names=required_names,
            WithDecryption=False,
        )

        found = {p["Name"]: p["Value"] for p in response["Parameters"]}
        missing = sorted(set(required_names) - set(found))

        if missing:
            raise ValueError(f"Missing required SSM parameters: {missing}")

        return {
            "cluster": found[ECS_CLUSTER_NAME_PARAM],
            "mlflow_tracking_uri": found[MLFLOW_TRACKING_URI_PARAM],
            "task_definition": found[TASK_DEFINITION_PARAM],
            "subnets": found[SUBNETS_PARAM].split(","),
            "security_groups": [found[SECURITY_GROUP_PARAM]],
        }

    runtime_config = resolve_ecs_runtime_config()

    train_lightgbm_ecs = EcsRunTaskOperator(
        task_id="train_lightgbm_on_ecs",
        aws_conn_id="aws_default",
        cluster=runtime_config["cluster"],
        task_definition=runtime_config["task_definition"],
        launch_type="FARGATE",
        platform_version="LATEST",
        wait_for_completion=True,
        reattach=False,
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": runtime_config["subnets"],
                "securityGroups": runtime_config["security_groups"],
                "assignPublicIp": "DISABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": "ml-runtime",
                    "command": ["train-lightgbm"],
                    "environment": [
                        {"name": "AWS_REGION", "value": AWS_REGION},
                        {
                            "name": "MLFLOW_TRACKING_URI",
                            "value": runtime_config["mlflow_tracking_uri"],
                        },
                    ],
                }
            ]
        },
        execution_timeout=timedelta(hours=8),
    )

    runtime_config >> train_lightgbm_ecs