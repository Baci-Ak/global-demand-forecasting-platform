
# Production ML Platform — Local Development Playbook (Repo-Agnostic)

This is a reusable, step-by-step guide to set up a production-grade local ML/Data platform on a laptop.
It is **repo-agnostic**: you can use it for any project.

## What you will build (mental model)

You will create a local environment that mirrors core AWS building blocks:

- **Postgres** (like AWS RDS): stores operational metadata and MLflow tracking metadata
- **MinIO** (like AWS S3): stores files and artifacts (raw data “Bronze”, ML artifacts, reports)
- **MLflow**: experiment tracking + model registry metadata, with artifacts stored in MinIO
- **Audit tables**: your pipeline’s “flight recorder” (what ran, when, status, where data landed)
- **Smoke tests**: quick checks that prove the system is wired correctly end-to-end

Why this matters:
- You can develop locally with confidence.
- Switching to AWS later becomes a configuration change, not a rewrite.

---

## Architectural principle (why this setup is production-grade)

A production ML system has two categories of storage:

1) **Metadata stores** (small, structured)
- pipeline run logs
- MLflow tracking database tables
- data quality results

2) **Object storage** (large files)
- raw data (Bronze)
- model artifacts (pkl/pt files, plots)
- evaluation reports

Local equivalent:
- Metadata store → **Postgres**
- Object storage → **MinIO (S3 compatible)**

---

## Prerequisites

- macOS
- Docker Desktop installed and running
- Python 3.11+
- A terminal
- Optional: pgAdmin (recommended)

---

## Step 1 — Create a clean project folder

Create a folder and minimal structure:

```

my-project/
docs/
infra/
docker/
ingestion/
training/

````

Create root files:
- README.md
- .gitignore
- Makefile

Why:
- This structure scales as the system grows.

---

## Step 2 — Create a Python virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -V
````

Why:

* Keeps dependencies isolated and reproducible.

---

## Step 3 — Create a local `.env` file (do not commit it)

Create `.env` (example values):

```env
# Postgres
POSTGRES_USER=gdf
POSTGRES_PASSWORD=gdf_password
POSTGRES_DB=gdf_meta
POSTGRES_PORT=5432
POSTGRES_DSN=postgresql://gdf:gdf_password@localhost:5432/gdf_meta

# MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio_password
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio_password

# IMPORTANT: Host-run code uses localhost, containers can use service DNS like http://minio:9000
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000

# MLflow
MLFLOW_PORT=5001
MLFLOW_TRACKING_URI=http://localhost:5001
MLFLOW_ARTIFACT_BUCKET=mlflow-artifacts

# Data Lake buckets
BRONZE_BUCKET=demand-forecast-bronze
```

Why:

* Centralizes configuration and keeps secrets out of git.
* Makes it easy to switch environments later.

---

## Step 4 — Docker Compose: Postgres + MinIO + MLflow

Create `docker-compose.yml` with three services:

* postgres
* minio
* mlflow

Key design:

* MLflow backend store → Postgres
* MLflow artifact store → MinIO (S3-compatible)

Important gotcha:

* MLflow often needs a Postgres driver in the container (`psycopg2` or `psycopg`).
  Best practice is to build a small custom MLflow image that installs the dependency.

Example custom Dockerfile:

`docker/mlflow/Dockerfile`

```dockerfile
FROM ghcr.io/mlflow/mlflow:v2.14.3
RUN pip install --no-cache-dir psycopg2-binary==2.9.9 boto3==1.34.162
```

Why:

* Reproducible builds, no “works on my machine” surprises.

---

## Step 5 — Start services and verify UIs

Start:

```bash
docker compose up -d
docker compose ps
```

Verify:

* MLflow UI: [http://localhost:5001](http://localhost:5001)
* MinIO Console: [http://localhost:9001](http://localhost:9001)

Note:

* Postgres is not a website. Use pgAdmin or psql to connect.

---

## Step 6 — Create required buckets in MinIO (UI)

In MinIO Console (Buckets → Create Bucket):

* `mlflow-artifacts`
* `demand-forecast-bronze`

Why:

* MLflow needs an artifact bucket.
* Bronze bucket is where raw data lands.

---

## Step 7 — Create audit tables in Postgres

Create a dedicated schema (recommended):

* `audit`

Create tables:

* `audit.ingestion_runs`: track ingestion runs (STARTED/SUCCEEDED/FAILED)
* `audit.dq_runs`: track data-quality runs (STARTED/PASSED/FAILED)

Why:

* Pipelines need traceability as complexity grows.

---

## Step 8 — Add smoke tests (must-have)

Two smoke tests prove the platform is correctly wired:

### A) MLflow smoke test

A small script logs:

* a param + metric (to Postgres via MLflow)
* an artifact file (to MinIO)

Success means:

* MLflow ↔ Postgres works
* MLflow ↔ MinIO works

### B) Bronze upload smoke test

A small script uploads a local file to Bronze bucket.

Success means:

* your S3 client + MinIO endpoint are correct

---

## What changes when moving to AWS later

Local → AWS mapping:

* Postgres → RDS Postgres
* MinIO → S3
* Local Docker services → ECS/EKS
* `.env` secrets → AWS Secrets Manager / IAM roles

Key principle:

* If you keep the platform modular, moving to AWS is mostly configuration.

---

## Recommended next step (after platform works)

Only after this platform is stable, start real work:

* ingest real datasets into Bronze
* log ingestion runs into `audit.ingestion_runs`
* add data quality gates
* then build Silver/Gold (warehouse) and ML training

