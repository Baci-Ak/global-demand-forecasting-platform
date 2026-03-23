# AWS ML Runtime Plan

## Purpose

This document defines the runtime design for the production ML system in AWS.

It answers five operational questions:

1. where MLflow runs
2. where model training runs
3. where batch scoring runs
4. how MWAA triggers ML jobs
5. how forecasts are written back to the warehouse

This document is intentionally operational.

The modeling decisions were already defined in:

- `docs/ml_system_production_plan.md`

This document focuses on **runtime execution design**.

---

## 1. Runtime design principles

The production ML runtime must follow these principles:

- all authoritative execution happens in AWS
- notebooks are not production runtime
- MWAA orchestrates but does not perform heavy ML training itself
- model artifacts are stored in S3
- ML metadata is stored in RDS Postgres
- forecasts are written back to warehouse tables
- the public app reads production outputs rather than generating live forecasts

This keeps the system:

- reproducible
- scalable
- observable
- operationally safe

---

## 2. Production runtime components

## 2.1 MLflow

### Role

MLflow is the system of record for:

- experiments
- model artifacts
- model versions
- feature importance artifacts
- evaluation artifacts

### Production backing services

- backend metadata store: **RDS Postgres**
- artifact store: **S3**
  - `gdf-prod-mlflow-artifacts`

### Runtime location

MLflow should run as a dedicated AWS-hosted service.

Recommended first implementation:

- **ECS service** in private subnets

Why:

- always-on service
- easier to manage than embedding MLflow inside MWAA
- consistent endpoint for training/scoring jobs
- closer to production-grade separation of concerns

MLflow should **not** run inside MWAA.

MWAA jobs should connect to MLflow, not host it.

---

## 2.2 Training extract job

### Role

The training extract job prepares model-ready data inputs for training.

It reads from:

- `gold.gold_m5_daily_feature_mart`

and writes to:

- parquet artifacts in S3

This creates stable training input datasets.

### Runtime choice

Recommended:

- **ECS task launched on demand by MWAA**

Why:

- extract is batch work
- it does not need to be always-on
- it fits orchestration-by-trigger pattern
- it can later scale to partitioned or full-data extract jobs

---

## 2.3 Model training job

### Role

The model training job:

- reads training extracts from S3
- builds features
- runs backtesting
- trains candidate models
- logs metrics and artifacts to MLflow
- registers the resulting candidate model

### Runtime choice

Recommended first implementation:

- **ECS task launched on demand by MWAA**

Future option if training becomes heavier:

- **AWS Batch**

Why ECS first:

- simpler operational model
- good fit for first production version
- enough for current LightGBM-based training flow
- easier to wire to MWAA

### Important rule

MWAA should trigger the training job, but the heavy model training must run outside MWAA workers.

---

## 2.4 Batch scoring job

### Role

The scoring job:

- loads the promoted production model from MLflow
- loads latest historical context
- generates recursive 28-day forecasts
- writes forecasts back to the warehouse
- optionally stores a forecast artifact in S3

### Runtime choice

Recommended:

- **ECS task launched on demand by MWAA**

This keeps training and scoring operationally symmetric.

---

## 2.5 Warehouse forecast writeback

### Role

Forecasts are written back into warehouse-facing forecast tables.

This is required so that:

- dashboards can query forecasts directly
- APIs can expose forecasts without running the model live
- monitoring can compare forecasts vs actuals
- forecast history becomes queryable and versioned

### Output destination

Production scoring should write to a dedicated warehouse forecast table, for example:

- `gold.gold_daily_demand_forecasts`

The exact table design will be specified later, but the architectural rule is fixed:

**forecast outputs must go back to the warehouse**

---

## 3. Orchestration design

## 3.1 MWAA responsibilities

MWAA is the orchestration layer.

It is responsible for:

- scheduling training extract jobs
- scheduling retraining jobs
- scheduling scoring jobs
- sequencing dependencies
- surfacing failures
- controlling cadence

MWAA is **not** responsible for:

- hosting MLflow
- storing model artifacts
- running heavy ML training workloads directly

---

## 3.2 Proposed DAG flow

### Retraining DAG

Recommended weekly flow:

1. verify Gold mart is refreshed
2. run training extract job
3. run training/backtesting job
4. log to MLflow
5. compare candidate against current production model
6. promote only if better and healthy

### Scoring DAG

Recommended daily flow:

1. verify Gold mart is refreshed
2. load promoted production model
3. run scoring job
4. write forecasts to warehouse
5. validate row counts and write success
6. log scoring run metadata

---

## 4. Cadence policy

## 4.1 Scoring cadence

Recommended:

- **daily**

Reason:

- demand forecasts should stay fresh
- 28-day horizon should roll forward regularly
- downstream dashboards and public app benefit from frequent refresh

## 4.2 Retraining cadence

Recommended:

- **weekly**

Reason:

- stable enough for retail demand forecasting
- avoids unnecessary churn
- gives space for evaluation and model comparison
- balances freshness and operational simplicity

### Promotion rule

Weekly retraining should not automatically replace production.

Instead:

- retrain candidate
- evaluate candidate
- compare against current production model
- promote only if better and operationally healthy

---

## 5. Public application relationship

The public app is a separate layer.

It should:

- read warehouse forecast outputs
- optionally call a lightweight API backed by warehouse queries
- never run training
- not depend on live recursive model execution

Recommended first public layer:

- **Streamlit**

Possible later public demo layer:

- **Hugging Face Spaces**

But the source of truth remains AWS production outputs.

---

## 6. Initial production runtime stack

The recommended first production runtime stack is:

- **MWAA** for orchestration
- **ECS service** for MLflow
- **ECS tasks** for training extract, model training, and scoring
- **RDS Postgres** for MLflow backend metadata
- **S3** for MLflow artifacts and training/forecast artifacts
- **Redshift** for forecast outputs and monitoring tables

This is the simplest production-grade architecture that matches the current platform.

---

## 7. Immediate implementation decisions

The next implementation work should follow this order:

### Step 1
Provision runtime host for MLflow in AWS.

### Step 2
Define how ECS tasks receive:
- warehouse DSN
- Postgres DSN
- MLflow tracking URI
- S3 artifact configuration

### Step 3
Containerize production ML jobs:
- training extract
- training
- scoring

### Step 4
Add MWAA orchestration for those jobs.

### Step 5
Create warehouse forecast output tables and writeback path.

---

## 8. Decision summary

The agreed AWS runtime design is:

- MLflow runs as a dedicated AWS-hosted service
- training extract runs as an ECS task
- model training runs as an ECS task
- batch scoring runs as an ECS task
- MWAA orchestrates those jobs
- forecasts are written back to Redshift
- public applications consume warehouse outputs, not live model execution