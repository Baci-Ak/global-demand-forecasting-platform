
# Developer Quickstart

This guide is the shortest reliable path to getting the Global Demand Forecasting Platform working locally and safely interacting with the deployed AWS environment.

It is intentionally practical. It does not repeat the full infrastructure, data platform, or ML platform documentation. It shows the correct order to get set up, connect to private services, run the platform, and know which document to open next when you need more detail.

## 📖 Contents

- [📌 What this quickstart covers](#-what-this-quickstart-covers)
- [🛠️ 1. Install the required tools](#️-1-install-the-required-tools)
- [🔐 2. Configure AWS access](#-2-configure-aws-access)
- [📦 3. Clone the repository](#-3-clone-the-repository)
- [🐍 4. Create the Python environments](#-4-create-the-python-environments)
- [⚙️ 5. Create the local environment file](#️-5-create-the-local-environment-file)
- [🏗️ 6. Make sure infrastructure access is in place](#️-6-make-sure-infrastructure-access-is-in-place)
- [🔌 7. Open private service tunnels](#-7-open-private-service-tunnels)
- [🗃️ 8. Prepare the audit database](#️-8-prepare-the-audit-database)
- [☁️ 9. Prepare MWAA runtime artifacts](#️-9-prepare-mwaa-runtime-artifacts)
- [🧱 10. Run the data platform](#-10-run-the-data-platform)
- [🤖 11. Run the ML platform](#-11-run-the-ml-platform)
- [📊 12. Run the forecast application](#-12-run-the-forecast-application)
- [✅ Common working rules](#-common-working-rules)
- [📚 Where to go next](#-where-to-go-next)

## 📌 What this quickstart covers

Use this guide when you want to:

- set up your local machine
- connect to the deployed AWS environment
- prepare the audit database
- upload MWAA runtime artifacts
- run the production data platform
- run the production ML platform
- run the forecast application locally

Use the detailed documents when you need deeper explanation:

- infrastructure: `docs/infrastructure.md`
- data platform: `docs/data-platform.md`
- ML platform: `docs/ml-platform.md`

## 🛠️ 1. Install the required tools

Install these first:

- Python 3.11
- AWS CLI v2
- Terraform
- Docker
- Git
- Make

Official references:

- [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS CLI configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
- [Terraform installation guide](https://developer.hashicorp.com/terraform/install)
- [pgAdmin download](https://www.pgadmin.org/download/)

## 🔐 2. Configure AWS access

After AWS CLI is installed, configure your terminal access:

```bash
aws configure
````

Set:

* AWS Access Key ID
* AWS Secret Access Key
* default region, usually `us-east-1`
* default output format

## 📦 3. Clone the repository

```bash
git clone https://github.com/Baci-Ak/global-demand-forecasting.git
cd global-demand-forecasting
```

## 🐍 4. Create the Python environments

This project uses two Python environments.

### Main runtime environment

Use `.venv` for:

* ingestion
* data quality
* warehouse loaders
* training and prediction
* MLflow-related code
* forecast application code
* general runtime development

Create it with:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### dbt environment

Use `.venv-dbt` for:

* dbt commands
* dbt model builds
* dbt tests

Create it with:

```bash
python3.11 -m venv .venv-dbt
source .venv-dbt/bin/activate
pip install --upgrade pip
pip install -r requirements-dbt.txt
```

## ⚙️ 5. Create the local environment file

Create `.env` from the example file:

```bash
cp .env.example .env
```

At minimum, set your AWS credentials and region:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
```

You will also need the correct DSNs and runtime values for:

* Postgres
* Redshift
* MLflow
* snapshot export

Use the relevant AWS secrets and the tunnel pattern described below.

## 🏗️ 6. Make sure infrastructure access is in place

Before using private access commands such as:

* `make connect-redshift`
* `make connect-postgres`
* `make connect-mwaa`
* `make connect-mwaa-mac`
* `make connect-mlflow`

make sure:

1. the infrastructure is already deployed
2. your AWS user has been added to the IAM user group:

   * `gdf-prod-engineer`

See [docs/infrastructure.md](infrastructure.md/) for the infrastructure deployment flow and the private access model.

## 🔌 7. Open private service tunnels

Core platform services are private.

That means local access works through tunnels and `localhost`, not through the private AWS hostname directly.

### Postgres

```bash
make connect-postgres
```

### Redshift

```bash
make connect-redshift
```

### MWAA

For macOS:

```bash
make connect-mwaa-mac
```

For other operating systems:

```bash
make connect-mwaa
```

### MLflow

```bash
make connect-mlflow
```

Keep the tunnel session open while your local client is connected.

## 🗃️ 8. Prepare the audit database

Before the data platform DAG can write ingestion and DQ audit records, the audit schema must exist in RDS Postgres.

### Step 1: open the Postgres tunnel

```bash
make connect-postgres
```

### Step 2: set the Postgres DSN in `.env`

Use the local tunnel endpoint:

```env
POSTGRES_DSN=postgresql://gdf_admin:password@localhost:5432/gdf_audit
AUDIT_SCHEMA=audit
```

### Step 3: run Alembic migrations

Activate `.venv` and run:

```bash
source .venv/bin/activate
make db-upgrade
```

You can also run:

```bash
alembic upgrade head
```

### Step 4: optional audit inspection in pgAdmin

While the tunnel is open, connect with:

* host: `localhost`
* port: `5432`
* username: from the RDS secret
* password: from `gdf/prod/rds-postgres/master`
* database: `gdf_audit`

## ☁️ 9. Prepare MWAA runtime artifacts

Before running the production DAGs, make sure MWAA has the required startup config and project package.

### Upload the startup configuration

If `orchestration/airflow/startup/gdf_runtime.conf` has changed:

```bash
make mwaa-upload-startup
```

### Build the project wheel

```bash
make mwaa-build-wheel
```

### Upload the wheel

```bash
make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
```

Use the actual filename if it changes.

### Upload all MWAA artifacts

```bash
make mwaa-upload-all
```

## 🧱 10. Run the data platform

The production data platform is orchestrated by MWAA through:

* `orchestration/airflow/dags/10_m5_full_refresh_mwaa.py`

### Before running it

Make sure:

* Kaggle credentials exist in Secrets Manager as `gdf/prod/kaggle_credentials`
* FRED API key exists in Secrets Manager as `gdf/prod/fred_api_key`
* the audit database migrations have been applied
* the MWAA startup config and wheel are uploaded

### Open MWAA

For macOS:

```bash
make connect-mwaa-mac
```

For other operating systems:

```bash
make connect-mwaa
```

### Trigger the DAG

In the Airflow UI, trigger:

* `10_m5_full_refresh_mwaa`

This runs the full production data platform flow:

1. ingest M5 data to Bronze
2. run M5 core DQ
3. load M5 core staging tables
4. ingest weather, macro, and trends data
5. run external-source DQ
6. load external-source staging tables
7. build and test dbt Silver
8. build and test dbt Gold

### Local data-platform work

For local work, common commands include:

```bash
make ingest-m5
make ingest-weather
make ingest-macro
make ingest-trends
make dq-all
make warehouse-stage-all
```

For dbt:

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

## 🤖 11. Run the ML platform

Only run the ML platform after the data platform has completed successfully and the Gold warehouse outputs are ready.

The production ML workflow runs in this order:

1. `20_export_training_extract_ecs`
2. `21_train_lightgbm_ecs`
3. `22_predict_next_28_days_ecs`

### What this does

* exports the production training extract
* trains the production LightGBM model in ECS
* logs training runs and artifacts to MLflow
* registers the model
* runs batch prediction for the next 28 days
* writes forecasts back to the warehouse

### Open MWAA

For macOS:

```bash
make connect-mwaa-mac
```

For other operating systems:

```bash
make connect-mwaa
```

Then trigger the three DAGs in order from the Airflow UI.

### Runtime image deployment

If the ML runtime image changed, push it from the project root:

```bash
make mlops-ci-push-ml-runtime
```

If the MLflow image changed:

```bash
make mlops-ci-push-mlflow
```

See `docs/ml-platform.md` for the full MLOps and image deployment flow.

## 📊 12. Run the forecast application

The forecast application only makes sense after the forecast table has been refreshed by the ML platform.

That means:

1. the data platform must be complete
2. the ML platform must have completed export, training, and prediction
3. the forecast writeback must already exist in the warehouse

### Export the latest application snapshot

With `.venv` active:

```bash
make export-forecast-app-snapshot
```

### Run the Streamlit app

```bash
streamlit run forecast_app/app.py
```

### Current runtime behavior

The application reads:

1. the latest snapshot from S3 first
2. the local cache second
3. an unavailable or empty state if neither is available

## Common working rules

* use `.venv` for runtime code
* use `.venv-dbt` for dbt
* use `localhost` when connecting to private AWS services from local tools
* keep the tunnel open while connected
* run the data platform before the ML platform
* run the ML platform before snapshot export and the forecast application
* update MWAA startup config and the wheel when runtime packaging changes

## 📚 Where to go next

Open these documents when you need the full detail:

- [infrastructure](./infrastructure.md)
- [data platform](./data-platform.md)
- [ML platform](./ml-platform.md)
