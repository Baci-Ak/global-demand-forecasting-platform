# Airflow Orchestration (Local-first, Production-shaped)

## Purpose
This folder contains everything needed to run Apache Airflow for this project.

We keep Airflow isolated under `orchestration/airflow/` so:
- the repo stays organized,
- the runtime is easy to understand for developers with no Airflow experience,
- the same structure can be reused for production deployment later (MWAA / ECS / EC2).

## Folder Layout
- `dags/`     : DAG definitions (the workflows Airflow runs)
- `plugins/`  : Custom Airflow operators/hooks (only if needed)
- `include/`  : SQL templates, docs, or assets used by DAGs
- `config/`   : Airflow configuration overrides (kept minimal)
- `logs/`     : Local logs (gitignored)

## How we will orchestrate this project
We will start by wrapping our existing working pipeline commands into Airflow tasks.
That lets Airflow handle:
- scheduling
- retries
- logs
- visibility of failures

We do NOT rewrite the pipeline logic at this stage.
