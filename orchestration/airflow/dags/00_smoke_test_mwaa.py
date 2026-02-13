from __future__ import annotations

from datetime import datetime
import os
import platform
import socket
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

DAG_START_DATE = datetime(2024, 1, 1)


def _print_runtime_context() -> None:
    # 
    print("MWAA smoke test starting ✅")

    print("\n=== Host (python) ===")
    print("socket.gethostname():", socket.gethostname())
    print("platform.node():", platform.node())

    print("\n=== Who am I? (env) ===")
    print("USER:", os.environ.get("USER"))
    print("HOME:", os.environ.get("HOME"))

    print("\n=== PWD ===")
    print("cwd:", os.getcwd())

    print("\n=== Python ===")
    print("executable:", sys.executable)
    print("version:", sys.version.replace("\n", " "))

    print("\n=== Airflow home ===")
    airflow_home = os.environ.get("AIRFLOW_HOME", "/usr/local/airflow")
    print("AIRFLOW_HOME:", airflow_home)

    # List a few entries safely (no shell tools).
    try:
        entries = sorted(os.listdir(airflow_home))[:50]
        print("AIRFLOW_HOME entries (first 50):")
        for e in entries:
            print("-", e)
    except Exception as exc:
        print("Could not list AIRFLOW_HOME:", repr(exc))

    print("\nMWAA smoke test complete ✅")


with DAG(
    dag_id="00_smoke_test_mwaa",
    description="MWAA smoke test: prove workers execute Python and task logs are emitted.",
    start_date=DAG_START_DATE,
    schedule=None,
    catchup=False,
    tags=["smoke", "mwaa"],
) as dag:
    PythonOperator(
        task_id="print_runtime_context",
        python_callable=_print_runtime_context,
    )
