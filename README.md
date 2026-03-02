# Global Retail Demand Forecasting (Production-Grade)

End-to-end demand forecasting + decision intelligence system:
**Bronze → Silver → Gold**, Feature Store (Feast), Training + Registry (MLflow),
Serving (FastAPI), Monitoring + Retraining, AWS deployment (Terraform).

## Docs (start here)
- **Project local setup (this repo):** `docs/00_project_local_setup.md`
- **Reusable platform playbook (from scratch, repo-agnostic):** `docs/platform/00_production_ml_platform_local_playbook.md`

## Current status
- Local platform spine working: Postgres + MinIO + MLflow
- Audit tables in Postgres: `audit.ingestion_runs`, `audit.dq_runs`
- Smoke tests:
  - `make test-mlflow`
  - Bronze upload smoke test via `ingestion/s3_client.py`

## Repo structure
- ingestion/        source collectors (Python)
- orchestration/    Airflow DAGs
- warehouse/        dbt (Silver/Gold on Redshift)
- quality/          Great Expectations
- feature_store/    Feast
- training/         PyTorch Lightning + Optuna + backtesting
- serving/          FastAPI inference
- dashboard/        Streamlit (initial)
- monitoring/       Evidently + metrics
- infra/            Terraform (AWS)
- docker/           Dockerfiles + compose
- docs/             runbooks + architecture + platform playbook

## Local commands
- `make up` / `make down` — start/stop local services
- `make ps` — show running containers
- `make logs` — follow logs
- `make test-mlflow` — end-to-end MLflow smoke test












┌──────────────┐
│   Kaggle     │   (external source)
└──────┬───────┘
       │
       ▼
┌────────────────────────────┐
│ Ingestion (Python)         │
│ - kaggle_client.py         │
│ - m5_ingestion.py          │
│ - audit_logger.py          │
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│ Bronze Layer (MinIO / S3)  │
│ demand-forecast-bronze     │
│ source=m5_sales/           │
│ ingest_date=YYYY-MM-DD/    │
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│ Data Quality (DQ)          │
│ - lake-native              │
│ - calendar checks          │
│ - Great Expectations–style │
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│ Postgres (Audit DB)        │
│ audit.ingestion_runs       │
│ audit.dq_runs              │
└────────────────────────────┘






## architecture (clean & correct)
        Kaggle
          |
          v
   [ Python ingestion ]
          |
          v
   ┌──────────────────┐
   │  Bronze (S3)     │  ← immutable raw files
   │  demand-forecast │
   └──────────────────┘
          |
          v
   [ Python loader ]
          |
          v
   ┌──────────────────┐
   │ staging.*        │  ← raw tables (db-native)
   └──────────────────┘
          |
          v
   [ dbt ]
          |
          v
   ┌──────────────────┐
   │ warehouse.*      │  ← curated analytics layer
   └──────────────────┘























# test
