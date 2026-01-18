
# 00 — Project Local Setup

This document explains how to run **this repository** locally.

If you are looking for a deep, reusable, step-by-step explanation of how the
local ML platform (Postgres + MinIO + MLflow) is built from scratch,
see the platform playbook:

➡️ `docs/platform/00_production_ml_platform_local_playbook.md`

---

## Quick start (this repo)

### 1) Clone the repository
```bash
git clone <repo-url>
cd global-demand-forecasting
````

### 2) Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Create `.env`

Create a `.env` file in the repo root.
A reference structure is documented in the platform playbook.

### 5) Start local services

```bash
make up
make ps
```

Verify:

* MLflow UI → [http://localhost:5001](http://localhost:5001)
* MinIO Console → [http://localhost:9001](http://localhost:9001)

### 6) Run smoke tests

```bash
make test-mlflow
```

Expected:

* MLflow experiment created
* Artifact written to MinIO

---

## What this enables next

Once local setup is complete, you can:

* ingest raw datasets into Bronze (S3/MinIO)
* log ingestion runs into `audit.ingestion_runs`
* build Silver/Gold warehouse layers
* train and register models with MLflow

