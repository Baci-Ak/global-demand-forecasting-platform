# AWS Warehouse Deployment Checklist (GDF)

## Goal
Deploy the full data warehouse stack to AWS so Gold tables are reliably built and testable on schedule.

## Target Architecture
- Bronze: S3
- Warehouse: Redshift
- Metadata/Audit DB: Postgres (RDS) OR Redshift (decision later)
- Orchestrator: Airflow
- Transform: dbt
- Observability: logs + metrics + alerting

## Environments
- dev (optional)
- staging (required)
- prod (later)

## Secrets / Config
- AWS credentials / IAM roles
- Redshift connection
- S3 bucket names
- dbt profile targets
- Airflow connections/variables

## Data Flow (end-to-end)
1. Ingest → S3 (Bronze)
2. Audit log ingestion_runs
3. DQ gate → audit dq_runs
4. Load staging tables in Redshift (COPY from S3)
5. dbt build Silver
6. dbt build Gold
7. dbt tests (contracts)
8. Publish docs (optional)

## Redshift Design Decisions
- Schemas: staging / silver / gold / audit?
- Dist keys / sort keys (especially for big fact tables)
- Table distribution strategy
- COPY options (CSV, gzip, manifest)

## Orchestration (Airflow DAG)
- Task order: ingest → dq → stage loads → dbt run → dbt test
- Retry policy
- SLAs (freshness expectations)

## Monitoring
- Pipeline failure alerts
- DQ failure alerts
- Freshness checks
- Row count deltas / anomaly detection

## Definition of Done
- One-click run of the DAG builds gold.gold_m5_training_daily in Redshift
- dbt tests pass in Redshift
- Failures produce audit trail + alert
