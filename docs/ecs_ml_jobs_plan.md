# ECS ML Jobs Plan

## Purpose

This document defines the ECS-based runtime design for production ML jobs in AWS.

It focuses on the batch jobs that MWAA will trigger for the ML system.

This document covers:

- training extract jobs
- model training jobs
- batch scoring jobs
- runtime configuration
- network and secret access
- how these jobs connect to MLflow, S3, and Redshift

This document does **not** define the modeling strategy itself.

That is already covered in:

- `docs/ml_system_production_plan.md`
- `docs/aws_ml_runtime_plan.md`

---

## 1. Why ECS is the right next step

The project already has:

- MWAA for orchestration
- Redshift for warehouse storage
- RDS Postgres for metadata
- S3 for artifacts
- private networking already in place

The missing runtime piece is a production compute target for ML jobs.

ECS is the correct first production choice because:

- it runs containerized batch jobs cleanly
- it integrates well with MWAA
- it supports private VPC execution
- it is simpler to operationalize than a heavier compute stack
- it can later be extended or replaced by AWS Batch if training becomes larger

So the first production runtime target will be:

**MWAA triggers ECS tasks for ML jobs**

---

## 2. Jobs that will run on ECS

The production ML system needs three ECS-driven batch jobs.

### 2.1 Training extract job

Purpose:

- read the model-ready Gold mart from the warehouse
- materialize a reproducible training extract
- write that extract to S3 as parquet

Input:

- `gold.gold_m5_daily_feature_mart`

Output:

- S3 parquet extract for training

Suggested command shape:

- Python module entrypoint
- for example:
  - `python -m training.data.export_training_extract`

This job becomes the first step in retraining.

---

### 2.2 Model training job

Purpose:

- read staged training extract from S3
- build features
- run backtesting
- train candidate model(s)
- log metrics and artifacts to MLflow
- register resulting model version

Input:

- training extract parquet in S3

Output:

- MLflow run
- MLflow model artifact
- MLflow registered model version
- optional evaluation artifacts in S3

Suggested command shape:

- Python module entrypoint
- for example:
  - `python -m training.pipelines.train_lightgbm`

This is the core retraining job.

---

### 2.3 Batch scoring job

Purpose:

- load promoted production model from MLflow
- load current historical context
- generate recursive 28-day forecasts
- write forecasts to warehouse output table
- optionally store a parquet copy in S3

Input:

- latest promoted production model
- latest historical source slice

Output:

- warehouse forecast table
- optional forecast artifact in S3

Suggested command shape:

- Python module entrypoint
- for example:
  - `python -m training.pipelines.predict_next_28_days`

This becomes the daily scoring job.

---

## 3. ECS runtime pattern

Each ML job should be implemented as:

- one container image
- one ECS task definition
- one command override per job type where needed

This keeps the system simple.

### Recommended pattern

One shared ML runtime image containing:

- project Python package
- training code
- db/warehouse connectors
- MLflow client
- LightGBM and supporting libraries

Then ECS tasks can run different commands such as:

- training extract
- train random forest
- train LightGBM
- scoring
- future monitoring tasks

This is better than building a separate container image for each job at the start.

---

## 4. Network design

The ECS ML jobs should run:

- in the same private VPC
- in private subnets
- with access to the shared workloads security group path where appropriate

They need private access to:

- Redshift
- RDS Postgres
- S3
- MLflow service

The ECS tasks should **not** require public internet access for core runtime behavior.

If external access is needed later, it should be explicit and controlled.

---

## 5. Secrets and configuration required by ECS jobs

Each ECS ML job will need environment variables and secrets for runtime.

### 5.1 Required connection/config values

These jobs will need:

- warehouse DSN
- Postgres DSN if needed
- MLflow tracking URI
- MLflow artifact bucket location
- AWS region
- model and feature-set configuration as needed

### 5.2 Source of truth

Use:

- **Secrets Manager** for sensitive values
- **task environment variables** for non-secret runtime config
- optionally **SSM Parameter Store** for non-secret operational coordinates

### 5.3 Core runtime secrets/config to provide

Expected set includes:

- `WAREHOUSE_DSN`
- `POSTGRES_DSN` if needed
- `MLFLOW_TRACKING_URI`
- `MLFLOW_ARTIFACT_BUCKET`
- `AWS_REGION`

If MLflow uses S3 directly, ECS tasks will also require IAM permissions for that artifact bucket.

---

## 6. MLflow runtime relationship

ECS jobs do not host MLflow.

Instead:

- MLflow runs as its own AWS-hosted service
- ECS jobs connect to MLflow using the configured tracking URI
- model artifacts are stored in:
  - `gdf-prod-mlflow-artifacts`

This separation is important.

It keeps:

- tracking stable
- jobs stateless
- runtime responsibilities clean

---

## 7. Warehouse writeback pattern

The batch scoring ECS task must write forecasts back to Redshift.

That means the scoring job should produce outputs shaped like:

- `store_id`
- `item_id`
- `forecast_date`
- `forecast_step`
- `prediction`
- run metadata later such as model version or scoring timestamp

The exact warehouse table schema can be finalized later, but the rule is fixed:

**ECS scoring jobs write forecasts back to the warehouse**

---

## 8. How MWAA uses ECS

MWAA remains the orchestrator.

### Retraining flow

1. confirm Gold mart is ready
2. trigger ECS training extract task
3. trigger ECS training task
4. wait for job completion
5. evaluate outcome
6. optionally promote model

### Scoring flow

1. confirm Gold mart is ready
2. trigger ECS scoring task
3. wait for completion
4. validate row counts / write success
5. log scoring success/failure

MWAA should not perform the heavy ML work itself.

It should trigger and supervise ECS tasks.

---

## 9. First implementation scope

The first ECS implementation should stay narrow and disciplined.

### Phase 1

Build ECS support for:

- training extract job
- LightGBM training job
- batch scoring job

Do **not** add extra model families or monitoring jobs to ECS first.

Get the first production path working end-to-end.

---

## 10. Immediate infrastructure implications

To support ECS ML jobs, the platform will need:

- ECS cluster or ECS-capable runtime environment
- task execution role
- task role with S3 / Redshift / RDS / MLflow access as needed
- task definition(s)
- container image repository, likely ECR
- MWAA permission to run ECS tasks
- private networking and security group access

---

## 11. Decision summary

The agreed design is:

- ECS will be the first production compute target for ML batch jobs
- MWAA will trigger ECS tasks
- ECS jobs will perform:
  - training extract
  - model training
  - batch scoring
- MLflow remains a separate service
- forecasts will be written back to the warehouse
- this is the production path that must be completed before the public app layer