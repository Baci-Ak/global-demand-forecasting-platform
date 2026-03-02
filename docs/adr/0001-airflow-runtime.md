# ADR 0001 — Airflow runtime target

## Status
Accepted

## Context
We need a production-grade orchestration runtime for the Global Demand Forecasting platform.
Local development runs Airflow via Docker Compose. CI validates code but does not orchestrate production runs.

## Decision
We will deploy Apache Airflow on AWS using **MWAA (Managed Workflows for Apache Airflow)**.

## Rationale
- Managed upgrades, scaling, patching (lower ops burden than ECS/EC2)
- AWS-native security model (VPC, IAM, CloudWatch)
- Standard enterprise path for production orchestration on AWS
- Keeps GitHub Actions focused on validation rather than scheduling

## Consequences
- DAGs and plugins will be deployed to an S3 bucket managed for MWAA.
- Runtime secrets will move to AWS-managed storage (Secrets Manager / SSM) rather than `.env`.
- Local Docker Airflow remains the developer environment for DAG iteration.
