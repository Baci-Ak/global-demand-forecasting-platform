
# 01 — Local Platform Setup (Postgres + MinIO + MLflow)

This document bootstraps the local foundation for the project:
- Postgres: metadata + audit tables (MLflow backend store + pipeline audit)
- MinIO: S3-compatible object storage (local stand-in for AWS S3)
- MLflow: experiment tracking + model registry metadata + artifacts

## Prerequisites
- macOS
- Docker Desktop installed and running
- Python 3.11+
- VS Code (optional)
- pgAdmin (optional but recommended)

## 1) Create Python virtual environment
From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -V
````

## 2) Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Start local services (Docker Compose)

```bash
make up
make ps
```

Services:

* MLflow UI: [http://localhost:5001](http://localhost:5001)
* MinIO Console: [http://localhost:9001](http://localhost:9001)
* Postgres: localhost:5432 (use a DB client; not a browser)

## 4) Create required MinIO buckets (UI)

Open MinIO Console: [http://localhost:9001](http://localhost:9001)
Login: minio / minio_password

Create buckets:

* mlflow-artifacts
* demand-forecast-bronze

## 5) Connect pgAdmin to Postgres (optional)

Connection details:

* Host: localhost
* Port: 5432
* Database: gdf_meta
* Username: gdf
* Password: gdf_password

Note: MLflow creates tables in the `public` schema.

## 6) Create audit schema + tables

SQL migrations are stored in `infra/sql/`.

Run these in pgAdmin Query Tool (or any SQL client) against `gdf_meta`:

* `infra/sql/001_create_audit_ingestion_runs.sql`
* `infra/sql/002_create_audit_dq_runs.sql`

Expected:

* `audit.ingestion_runs`
* `audit.dq_runs`

## 7) Validate end-to-end MLflow (1 command)

```bash
make test-mlflow
```

Expected:

* terminal prints: "MLflow test run completed successfully."
* in MLflow UI you see experiment `local_smoke_test` with an artifact `hello.txt`

## 8) Validate Bronze uploads (optional smoke test)

Run:

```bash
python -c "from pathlib import Path; from datetime import date; from ingestion.s3_client import upload_file_to_bronze; p=Path('local_smoke.txt'); p.write_text('bronze upload works'); key=f'source=smoke_test/ingest_date={date.today().isoformat()}/local_smoke.txt'; print(upload_file_to_bronze(p, key))"
```

Verify in MinIO bucket `demand-forecast-bronze`:

* `source=smoke_test/ingest_date=YYYY-MM-DD/local_smoke.txt`

## Notes on config

Local settings are stored in `.env` (not committed).

* Host-run code uses `http://localhost:9000` for MinIO endpoint
* Docker containers can use `http://minio:9000` internally

In AWS deployment, secrets move to AWS Secrets Manager / IAM roles.
