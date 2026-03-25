# Data Platform

This document describes the data platform of the Global Demand Forecasting Platform.

It covers source setup, raw data landing, audit and migration prerequisites, local execution, MWAA execution, the end-to-end production DAG, and the deployment steps required to keep the data platform runnable in AWS.

This document is focused on the data platform only.

## What the data platform does

The data platform is responsible for:

- sourcing the raw input data
- landing raw data in Bronze on S3
- recording ingestion audit metadata
- validating raw data before warehouse loading
- recording data quality audit metadata
- loading Redshift staging tables
- building dbt Silver models
- building dbt Gold models
- producing the curated warehouse outputs that feed the ML platform

At a high level, the data platform flow is:

1. source access is configured
2. raw data is ingested into Bronze on S3
3. ingestion runs are written to the audit database
4. data quality checks run against Bronze data
5. DQ runs are written to the audit database
6. validated data is loaded into Redshift staging
7. dbt builds Silver
8. dbt builds Gold
9. Gold outputs become the input to the ML platform

## Source integrations

The implemented source families are:

- M5 retail demand data
- weather data
- macroeconomic data from FRED
- search trends data from Google Trends

## External source setup

Two external source credentials must be prepared before the full production data platform can run successfully.

### Kaggle credentials for M5 data

The M5 source access path uses Kaggle.

To create the Kaggle API token:

1. sign in to Kaggle
2. open your account settings
3. go to the API section
4. create a new API token
5. download the `kaggle.json` file

Official Kaggle references:

- [Kaggle API documentation](https://www.kaggle.com/docs/api)
- [Kaggle getting started guide for API authentication](https://www.kaggle.com/getting-started/524433)

For production, store the Kaggle credentials in AWS Secrets Manager as:

- `gdf/prod/kaggle_credentials`

Store it as plaintext JSON in this shape:

```json
{
  "KAGGLE_USERNAME": "your_kaggle_username",
  "KAGGLE_API_TOKEN": "your_api_token",
  "M5_COMPETITION": "m5-forecasting-accuracy"
}
````

### FRED API key for macro data

The macro source access path uses the FRED API.

To create a FRED API key:

1. create or sign in to your FRED account
2. request an API key
3. copy the issued key

Official FRED references:

* [FRED API key documentation](https://fred.stlouisfed.org/docs/api/api_key.html)
* [FRED API overview](https://fred.stlouisfed.org/docs/api/fred/)

For production, store the FRED API key in AWS Secrets Manager as:

* `gdf/prod/fred_api_key`

Store it as plaintext.

## Runtime configuration used by MWAA

The MWAA startup configuration file is:

```text 
orchestration/airflow/startup/gdf_runtime.conf
```

This file holds the non-secret runtime configuration used by MWAA startup and points MWAA to:

* the runtime config file in S3
* the packaged wheel in S3
* the Secrets Manager identifiers for Postgres and warehouse access
* the Bronze bucket
* the Kaggle secret
* the FRED secret
* the staging and dbt settings
* the source configuration values used by the data platform

For the data platform specifically, this file includes:

* `POSTGRES_DSN_SECRET_ID=gdf/prod/postgres_dsn`
* `WAREHOUSE_DSN_SECRET_ID=gdf/prod/warehouse_dsn`
* `REDSHIFT_ADMIN_SECRET_ID=gdf/prod/redshift/admin`
* `BRONZE_BUCKET=gdf-prod-bronze-697980229152`
* `KAGGLE_SECRET_ID=gdf/prod/kaggle_credentials`
* `MACRO_SECRET_ID=gdf/prod/fred_api_key`

Whenever this file is changed, upload the updated startup artifacts again so MWAA can use the new runtime configuration.

## Audit database prerequisite

Before running the platform DAGs, the audit tables must exist in RDS Postgres.

The audit schema is managed through Alembic.

That means a working data-platform setup must include the audit database migration step before expecting ingestion and DQ audit writes to succeed.

## Local audit database setup

To prepare the audit database locally against the private RDS Postgres instance:

1. ensure the infrastructure is already deployed
2. ensure your AWS user has the required access group membership as described in `docs/infrastructure.md`
3. open the Postgres tunnel from the project root
4. set the local Postgres DSN in `.env`
5. run the Alembic migration

Open the tunnel:

```bash 
make connect-postgres
```

In your local `.env`, make sure these values exist:

```env 
POSTGRES_DSN=postgresql://gdf_admin:password@localhost:5432/gdf_audit
AUDIT_SCHEMA=audit
```

Then activate the main Python environment and run the migration:

```bash 
source .venv/bin/activate
pip install -r requirements.txt
make db-upgrade
```

You can also run:

```bash 
alembic upgrade head
```

if you want to execute Alembic directly.

## Viewing the audit database locally

If you want to inspect the audit database from a desktop client, use pgAdmin or another PostgreSQL client while the tunnel is open.

Official pgAdmin download page:

* [pgAdmin download](https://www.pgadmin.org/download/)

For local access through pgAdmin:

* host: `localhost`
* port: `5432`
* username: from the RDS-related secret in AWS Secrets Manager
* password: from `gdf/prod/rds-postgres/master`
* database: `gdf_audit` or the database defined in the DSN you are using

The tunnel must remain open while the client is connected.

## Local developer setup for the data platform

Before running the data platform locally, complete these steps:

1. install Python 3.11
2. create and activate `.venv`
3. install the runtime dependencies
4. create `.env`
5. set AWS credentials in `.env`
6. set the local Postgres DSN and warehouse DSN in `.env`
7. open the required private tunnels when working against AWS services

Typical local setup:

```bash 
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

For dbt work, also create and use `.venv-dbt` separately.


Create it with:

```bash
python3 -m venv .venv-dbt
source .venv-dbt/bin/activate
pip install --upgrade pip
pip install -r requirements-dbt.txt
```



Use `.venv` for:

* ingestion
* data quality
* warehouse loaders
* training and prediction
* MLflow-related code
* forecast application code
* general runtime development

Use `.venv-dbt` for:

* dbt commands
* dbt model builds
* dbt tests





## Local data-platform execution

The main local execution areas are:

* ingestion
* DQ
* staging loads
* dbt Silver
* dbt Gold

### Ingestion commands

From the project root with `.venv` active, the source ingestion commands are:

```bash 
make ingest-m5
make ingest-weather
make ingest-macro
make ingest-trends
```

### Data quality commands

The source-specific DQ commands are:

```bash
make dq-calendar
make dq-sell-prices
make dq-sales-train-validation
make dq-weather-daily
make dq-macro-series
make dq-trends-interest-over-time
```

Or run them together with:

```bash
make dq-all
```

### Warehouse staging commands

Open the tunnel:

```bash
make connect-mwaa
```
or for macos users:

```bash
make connect-mwaa-mac
```

In `.env`, make sure these value exist:

```env
WAREHOUSE_DSN=postgresql://admin:password@localhost:5439/warehouse
```
The staging loaders are exposed through:

```bash
make warehouse-load-calendar
make warehouse-load-sell-prices
make warehouse-load-sales-train-validation
make warehouse-load-weather-daily
make warehouse-load-macro-series
make warehouse-load-trends-interest-over-time
```

Or run the full staging set with:

```bash 
make warehouse-stage-all
```

### dbt Silver and Gold

Run dbt from the dbt environment:

```bash
source .venv-dbt/bin/activate
cd warehouse
dbt debug --profiles-dir .dbt
dbt run --select models/silver --profiles-dir .dbt
dbt test --select models/silver --profiles-dir .dbt
dbt run --select models/gold --profiles-dir .dbt
dbt test --select models/gold --profiles-dir .dbt
cd ..
```

## MWAA deployment steps for the data platform

If the MWAA runtime config or package changes, update MWAA in this order.

### Upload updated startup configuration

After updating `orchestration/airflow/startup/gdf_runtime.conf`, upload it with:

```bash
make mwaa-upload-startup
```

### Build and upload the project wheel

Build the platform wheel:

```bash
make mwaa-build-wheel
```

Upload the wheel:

```bash
make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
```

Use the actual wheel filename if it changes.

### Upload the rest of the MWAA artifacts

To upload DAGs, requirements, plugins, and startup files together:

```bash
make mwaa-upload-all
```

## The production data-platform DAG

The main production data-platform DAG is:

```text
orchestration/airflow/dags/10_m5_full_refresh_mwaa.py
```

This DAG orchestrates the end-to-end batch data platform on MWAA.

### What the DAG runs

The implemented workflow in the DAG is:

1. ingest M5 data to Bronze and write ingestion audit records
2. run M5 core DQ checks
3. load M5 core staging tables
4. ingest weather data to Bronze
5. ingest macro data to Bronze
6. ingest trends data to Bronze
7. run DQ for weather
8. run DQ for macro
9. run DQ for trends
10. load weather staging
11. load macro staging
12. load trends staging
13. build and test dbt Silver
14. build and test dbt Gold

### DAG ownership and execution model

The DAG follows the project’s operating rule:

* Airflow orchestrates the workflow
* Airflow does not reimplement the pipeline logic

The tasks call the same underlying Python and dbt entrypoints used by developers locally.

### Task order

At a dependency level, the DAG flows like this:

* `ingest_m5_to_bronze`
* `dq_m5_core`
* `warehouse_stage_m5_core`

then branches into:

* weather ingestion, DQ, and staging
* macro ingestion, DQ, and staging
* trends ingestion, DQ, and staging

and finally converges into:

* `dbt_silver_build_and_test`
* `dbt_gold_build_and_test`

### Warehouse pool note

The DAG expects a pool named `warehouse_pool` for the warehouse staging and dbt tasks.

Create it in the Airflow UI if it does not already exist.

Use:

* pool name: `warehouse_pool`
* slots: `1` or another value that matches your intended warehouse concurrency

## Running the DAG in MWAA

MWAA is private and must be accessed through the tunnel pattern.

For macOS:

```bash
make connect-mwaa-mac
```

For other operating systems:

```bash
make connect-mwaa
```

Once the tunnel is open, open the MWAA / Airflow UI and trigger:

* `10_m5_full_refresh_mwaa`

This is the main end-to-end production run for the data platform.

## Data-platform CI/CD

The data platform deployment path to MWAA depends on GitHub environment configuration.

### GitHub environment setup

In GitHub:

1. open the repository
2. go to `Settings`
3. open `Environments`
4. create the `prod` environment if it does not already exist

### AWS role for GitHub Actions

In AWS:

1. open IAM
2. open Roles
3. find `gdf-prod-github-actions`
4. copy its ARN

Example format:

```text
arn:aws:iam::697980229152:role/gdf-prod-github-actions
```

Back in the GitHub `prod` environment, create the secret:

* `AWS_ROLE_ARN`

using that role ARN as the value.

### GitHub environment variables

In the same GitHub `prod` environment, create these environment variables:

* `AWS_REGION`
* `MWAA_BUCKET`
* `MWAA_ENV_NAME`

For example:

* `AWS_REGION=us-east-1`
* `MWAA_BUCKET=gdf-prod-airflow-697980229152`
* `MWAA_ENV_NAME=gdf-prod-mwaa`

### Deployment flow

After committing the required changes, manually run the GitHub workflow:

* `Prod - Deploy to MWAA (manual)`

Use it when you want to push updated DAGs and related artifacts, or when you need the deployment pipeline to refresh the MWAA environment state.

## Main repository areas for the data platform

The main repository areas for the data platform are:

* `ingestion/`
* `quality/`
* `warehouse/loaders/`
* `warehouse/models/`
* `warehouse/tests/`
* `audit_log/`
* `database/`
* `alembic/`
* `orchestration/airflow/dags/10_m5_full_refresh_mwaa.py`
* `orchestration/airflow/startup/gdf_runtime.conf`

## Relationship to the ML platform

The data platform ends at curated Gold warehouse outputs.

The ML platform starts from those outputs and is responsible for training extract generation, model training, model registration, batch prediction, and forecast writeback.

## Related documents
- [README.md](../README.md)
- [data platform](./infrastructure.md)
- [infrastructure](./ml-platform.md)
- [data platform](./developer-quickstart.md)