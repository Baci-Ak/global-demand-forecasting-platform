# ML System Production Plan

## Purpose

This document defines the production-grade ML system design for the Global Demand Forecasting platform.

It is the bridge between:

- local notebook and benchmark experimentation
- the current MLOps prototype
- the final AWS production system
- the public-facing forecast application layer

The goal is to keep the system:

- reproducible
- scalable
- observable
- maintainable
- safe for future extension by other data scientists and ML engineers

---

## 1. Current state

The project already has the following working components.

### Data platform

- ingestion pipelines for M5, weather, macro, and trends
- Bronze, Silver, and Gold layers
- dbt transformations
- data quality checks
- orchestration foundation in MWAA direction
- warehouse-ready Gold modeling mart:
  - `gold.gold_m5_daily_feature_mart`

### Modeling and MLOps prototype

- notebook-based problem framing, EDA, and baseline development
- benchmark model training package under `training/`
- MLflow experiment tracking
- MLflow model registry
- recursive forecasting prototype
- batch forecast artifact generation
- first reproducible training extract artifact

### Current best benchmark model

Current leading benchmark candidate:

- model family: **LightGBM**
- feature set: **calendar_lag_rolling_baseline**
- evaluation mode: **5 rolling windows**
- benchmark scope: **top-20 item-store series subset**

Current benchmark metrics:

- average WMAPE: **0.2090**
- average MAE: **10.3662**
- average RMSE: **14.9019**

This is a strong benchmark, but it is **not yet the final production model**, because it has not yet been trained and validated on the full dataset in production-grade compute.

---

## 2. Key production design decision

The real production ML system will run in **AWS**.

The public-facing user experience will be a **separate presentation layer** built on top of warehouse-stored forecasts.

### Production system

The production system is responsible for:

- training
- retraining
- model tracking
- model registry
- batch inference
- writing forecasts back to the warehouse
- monitoring model behavior and forecast quality

### Public-facing application

The public application is responsible for:

- reading already-generated forecasts
- presenting results to users
- exposing forecast outputs through a UI or API
- never becoming the source of truth for model execution

This separation is required for a production-grade forecasting system.

---

## 3. Environment mapping: local to production

The local system is a development mirror of the AWS production design.

| Local development | Production AWS equivalent |
|---|---|
| Docker Postgres | RDS Postgres |
| Docker MinIO | S3 |
| Docker MLflow | MLflow in AWS |
| Local warehouse / Postgres | Redshift |
| Notebook execution | AWS training and scoring jobs |
| Local parquet artifacts | S3 training and forecast artifacts |

This means the local environment remains valuable for:

- iteration
- debugging
- reproducibility testing
- development of training and inference code

But full production execution must happen in AWS.

---

## 4. Production architecture

## 4.1 Source data and warehouse

The warehouse remains the central data source for the ML system.

Flow:

1. raw data lands in Bronze
2. cleaned data is transformed in Silver
3. business-ready and ML-ready tables are built in Gold
4. the ML system reads model inputs from Gold
5. forecasts are written back into warehouse-facing forecast tables

Primary training source table:

- `gold.gold_m5_daily_feature_mart`

Primary forecast output destination:

- a warehouse forecast table to be created for production output

---

## 4.2 Model tracking and registry

MLflow will remain the experiment tracking and model registry system.

### MLflow backend store

Use:

- **RDS Postgres**

Purpose:

- experiment metadata
- run metadata
- model registry metadata
- lineage information

### MLflow artifact store

Use:

- **S3**

Purpose:

- model artifacts
- feature importance artifacts
- evaluation artifacts
- run-level outputs

This means production infrastructure must include an S3 bucket dedicated to MLflow artifacts.

---

## 4.3 Training data staging

The production training system must not train directly from ad hoc notebook queries.

Instead, the correct pattern is:

1. warehouse extract step reads from Gold
2. training extract is written to parquet in S3
3. training job consumes the staged parquet input

Benefits:

- reproducibility
- stable input contracts
- reduced coupling between model code and direct warehouse queries
- easier full-data training
- easier backfill and rerun behavior

---

## 4.4 Training compute

Full-data production training must run outside notebooks.

Recommended execution pattern:

- MWAA orchestrates training
- a dedicated AWS compute job executes the training code
- the job reads training extract artifacts from S3
- the job writes metrics/artifacts to MLflow
- the job registers or updates candidate models

Recommended compute choice:

- **ECS task** first
- move to **AWS Batch** later if heavier training compute becomes necessary

Rationale:

- ECS is a clean first production step
- it fits batch-oriented execution
- it integrates well with MWAA
- it is simpler to operationalize before adding heavier distributed compute

---

## 4.5 Batch inference

Demand forecasting in this project is a **batch inference** problem, not a realtime inference problem.

Forecasts will be generated on a schedule.

Flow:

1. MWAA triggers scoring job
2. scoring job loads the promoted production model from MLflow
3. scoring job reads latest model input data
4. recursive 28-day forecasts are generated
5. forecasts are written back to warehouse tables
6. optional forecast artifact copy is saved to S3

This is the correct architecture for retail demand forecasting.

---

## 4.6 Warehouse forecast outputs

Forecasts must be written back to the warehouse.

This is a core architectural rule.

Why:

- dashboards can read forecasts directly
- APIs can expose forecasts without running models live
- forecast history becomes queryable
- actual-vs-forecast analysis becomes easier
- monitoring becomes much easier
- warehouse remains the analytics system of record

The public application layer should read from warehouse-served forecast outputs, not generate live forecasts itself.

---

## 4.7 Monitoring

Production monitoring must cover both pipeline health and model behavior.

### Pipeline monitoring

- training job success/failure
- scoring job success/failure
- row counts
- missing forecasts
- artifact write success
- warehouse writeback success

### Model monitoring

- forecast distribution shifts
- actual vs forecast error over time
- model stability over retrains
- feature drift signals later if needed

Monitoring outputs should be written to warehouse-accessible monitoring tables so that dashboards and alerts can be built on top.

---

## 5. Training and scoring cadence

The model should not retrain on every scoring run.

Recommended initial cadence:

### Scoring cadence

- **daily**

Purpose:

- keep forecasts fresh
- maintain the 28-day rolling forecast horizon
- support downstream dashboards and public app freshness

### Retraining cadence

- **weekly**

Purpose:

- update the model with newer data
- compare candidate performance to the current production model
- avoid unnecessary retraining churn

Promotion rule:

- retrain weekly
- evaluate candidate
- promote only if better and healthy
- otherwise keep the current production model

This is the safest first production policy.

---

## 6. Deployment layers

The final system has two deployment layers.

### Layer 1: real production ML system

Location:

- **AWS**

Responsibilities:

- training
- retraining
- registry
- batch inference
- forecast writeback
- monitoring

### Layer 2: public-facing forecast application

Possible technologies:

- **Streamlit**
- **FastAPI**
- later optionally **Hugging Face Spaces**

Responsibilities:

- browse forecasts
- display actual vs forecast
- expose model version
- expose forecast outputs
- provide user-facing interface

This layer must consume production outputs, not replace the production ML system.

---

## 7. Recommended technology choices

Recommended production stack:

- warehouse: **Redshift**
- orchestration: **MWAA**
- experiment tracking: **MLflow**
- ML metadata database: **RDS Postgres**
- artifact store: **S3**
- training compute: **ECS task first**
- heavier future training option: **AWS Batch**
- model family: **LightGBM** as current leading candidate
- forecast serving mode: **batch**
- public app: **Streamlit first**
- optional later public demo surface: **Hugging Face Spaces**

---

## 8. Current production-readiness status

### Already complete

- core data platform
- external feature integration
- warehouse Gold mart
- benchmark training package
- MLflow tracking
- model registry
- rolling backtesting
- recursive forecasting prototype
- batch forecast artifact output

### Not yet complete

- AWS MLflow production deployment
- production S3 artifact bucket(s)
- production training extract pipeline
- full-data training in AWS compute
- warehouse forecast writeback pipeline
- retraining orchestration
- monitoring tables and alerts
- public-facing application layer

---

## 9. Implementation order from here

The work should proceed in this order.

### Phase 1 — lock production design
- finalize this production plan
- keep all implementation aligned to it

### Phase 2 — provision AWS ML infrastructure
- add S3 bucket for MLflow artifacts
- add S3 location for training extracts
- add S3 location for forecast artifacts if needed
- wire MLflow backend/artifact configuration for AWS

### Phase 3 — production training path
- build warehouse-to-parquet training extract pipeline
- run full-data training in AWS compute
- log runs to MLflow
- register candidate model versions

### Phase 4 — production inference path
- build scheduled batch scoring job
- write forecasts back to warehouse tables
- version forecast outputs

### Phase 5 — monitoring and governance
- add forecast monitoring tables
- add retraining comparison logic
- add promotion rules and rollback path

### Phase 6 — public application layer
- build Streamlit or FastAPI app
- read forecasts from warehouse outputs
- expose user-facing forecast experience

---

## 10. Decision summary

The agreed production direction is:

- **train in AWS**
- **score in AWS**
- **track with MLflow**
- **store artifacts in S3**
- **write forecasts back to the warehouse**
- **serve public experience from a separate app layer**

The next implementation work will focus on AWS production ML infrastructure, not public deployment yet.