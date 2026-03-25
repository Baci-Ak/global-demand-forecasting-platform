# ML Platform

This document describes the MLOps and ML platform of the Global Demand Forecasting Platform.

It covers the production ML workflow, training extract generation, ECS runtime execution, MLflow tracking and model registry, forecast writeback, monitoring outputs, local developer workflow, MWAA orchestration, and deployment steps for the ML runtime and MLflow images.

This document is focused on the ML platform only.

## What the ML platform does

The ML platform starts after the data platform has produced the curated Gold warehouse outputs.

Its responsibility is to:

- export the production training extract from the warehouse
- run model training in the shared ECS ML runtime
- track runs and artifacts in MLflow
- register the trained model in MLflow
- run batch prediction for the next 28 days
- write forecasts back to the warehouse
- expose warehouse-native monitoring outputs for forecast runs and freshness
- provide the forecast outputs consumed by the snapshot export layer

At a high level, the ML platform flow is:

1. the data platform builds the Gold warehouse models
2. a training extract is exported from Redshift to S3
3. the ECS ML runtime trains the production model
4. MLflow records the run, artifacts, and model registration state
5. the ECS ML runtime runs batch prediction using the latest trained model
6. forecasts are written back to the warehouse
7. warehouse monitoring views expose forecast run status and freshness
8. the forecast application layer can export snapshots from those warehouse outputs




## MLOps operating model

The ML platform follows a clear separation of responsibilities.

MWAA is the orchestrator. ECS performs the heavy runtime work. MLflow is the system of record for experiment tracking and model registry state. Redshift remains the warehouse source for curated model-ready inputs and the destination for forecast writeback.

In practice, the operating model is:

- the data platform prepares the curated Gold warehouse layer
- MWAA schedules and supervises the ML workflow
- ECS / Fargate runs the shared ML runtime container
- MLflow records runs, artifacts, and model registration state
- Redshift stores the forecast outputs and monitoring views

This separation keeps orchestration, compute, tracking, and warehouse serving responsibilities clean.

### Runtime execution pattern

The ECS-based DAGs do not hardcode live runtime coordinates inside the DAG body.

Instead, they resolve required values from AWS Systems Manager Parameter Store at task runtime, including:

- ECS cluster name
- MLflow tracking URI
- ECS task definition family
- private subnet IDs
- security group ID

This keeps the orchestration layer environment-aware without making the DAGs brittle.

### Command-based shared runtime

The production ML platform uses one shared runtime image and switches behavior through container command overrides.

The main production commands are:

- `export-training-extract`
- `train-lightgbm`
- `predict-next-28-days`

This is the core MLOps runtime pattern in the project.


## Core platform components

The ML platform depends on these core services:

- Redshift
- S3
- ECS / Fargate
- MLflow
- RDS Postgres
- MWAA / Airflow
- ECR

Each service has a distinct role in the production workflow.

### Redshift

Redshift is the source of the curated training data and the destination of forecast writeback.

The ML platform uses Redshift for:

- reading the Gold training-ready warehouse outputs
- exporting the production training extract
- persisting forecast outputs
- exposing monitoring views for run status and forecast freshness

### S3

S3 is used by the ML platform for:

- training extract storage
- MLflow artifact storage
- packaged runtime assets and deployment artifacts where needed

### ECS / Fargate

The heavy compute work is performed in ECS, not in MWAA.

The ECS ML runtime is used for:

- training extract export
- model training
- batch prediction

### MLflow

MLflow is the experiment tracking and model registry service for the platform.

It is used for:

- experiment tracking
- artifact logging
- model registration
- retrieving the latest trained model for prediction

### RDS Postgres

RDS Postgres stores the MLflow metadata backend.

This separates ML system metadata from the analytical warehouse.

### MWAA / Airflow

MWAA orchestrates the ML platform.

It schedules and coordinates the ECS-based runtime jobs, but it does not perform the heavy ML compute itself.

### ECR

ECR stores the production container images used by:

- the ECS ML runtime
- the MLflow service image

## Production ML workflow

The implemented production ML workflow is split into three main orchestration steps.

### 1. Export the training extract

The first step exports the production training extract from Redshift to S3.

This is orchestrated by the DAG:

- `orchestration/airflow/dags/20_export_training_extract_ecs.py`

This DAG:

1. resolves ECS runtime coordinates from SSM Parameter Store at task runtime
2. launches the shared ML runtime container on ECS / Fargate
3. overrides the container command to run `export-training-extract`
4. waits for completion and surfaces failures in Airflow and CloudWatch

This step exists so model training runs against a consistent production extract rather than querying the warehouse ad hoc inside the training job.

### 2. Train the production model

The second step runs production LightGBM training.

This is orchestrated by the DAG:

- `orchestration/airflow/dags/21_train_lightgbm_ecs.py`

This DAG:

1. resolves ECS runtime coordinates from SSM at task runtime
2. launches the shared ML runtime container on ECS / Fargate
3. overrides the container command to run `train-lightgbm`
4. waits for completion and surfaces failures in Airflow and CloudWatch

This step trains the production model and records the training run in MLflow.

### 3. Run batch prediction

The third step runs batch forecasting for the next 28 days.

This is orchestrated by the DAG:

- `orchestration/airflow/dags/22_predict_next_28_days_ecs.py`

This DAG:

1. resolves ECS runtime coordinates from SSM at task runtime
2. launches the shared ML runtime container on ECS / Fargate
3. overrides the container command to run `predict-next-28-days`
4. waits for completion and surfaces failures in Airflow and CloudWatch

This step uses the production model and writes forecast outputs back to the warehouse.






## Model selection and production feature set

The production ML path uses the Gold warehouse table:

- `gold.gold_m5_daily_feature_mart`

This is the model-ready warehouse dataset used by the training extract flow and, from there, the training and prediction runtime.

## Training extract contract

The production training extract is intentionally bounded.

The current extract contract is defined to:

- use the most recent 365 days of history
- export from `gold.gold_m5_daily_feature_mart`
- publish the extract to the stable S3 prefix `ml/training_extracts/full`
- keep the current runtime within the present ECS and pandas memory envelope

The current production configuration also keeps the training universe bounded to a top-series subset during extract generation, using the configured series limit in the training extract configuration.

This is an operational design choice. It keeps production retraining repeatable and within the current compute boundary.

## Feature-set experiments

The project includes a registered set of approved feature-set experiments in the training feature engineering layer.

The implemented feature-set families are:

- `calendar_lag_rolling_baseline`
- `baseline_plus_price`
- `baseline_plus_weather`
- `baseline_plus_macro`
- `baseline_plus_trends`
- `full_feature_set`

The current production feature set is:

- `calendar_lag_rolling_baseline`

This is the default in both the training and prediction configuration.

## What `calendar_lag_rolling_baseline` contains

The production feature set is made up of two groups:

### Calendar features

These are derived directly from the daily date field:

- `day_of_week`
- `day_of_month`
- `week_of_year`
- `month`

These variables capture repeating calendar structure in the daily sales pattern.

### Lag and rolling features

These are derived from each `store_id` and `item_id` series in a leakage-safe way.

The production lag features are:

- `lag_1`
- `lag_7`
- `lag_28`

These are created by grouping by:

- `store_id`
- `item_id`

and shifting the historical `sales` series backward by 1, 7, and 28 days.

The production rolling features are:

- `rolling_mean_7`
- `rolling_mean_28`

These are also derived within each `store_id` and `item_id` series.

They are computed from lagged sales history, using `shift(1)` before the rolling window is calculated, so the current day’s target is never included in its own features.

That detail matters. It keeps the features leakage-safe for both backtesting and production forecasting.

## External feature families that were tested

The project also tested broader feature families drawn from the same Gold mart.

These include:

### Price features

- `sell_price_filled`
- `sell_price_missing_flag`

### Weather features

- `temperature_2m_max`
- `temperature_2m_min`
- `precipitation_sum`
- `wind_speed_10m_max`

### Macro features

- `cpi_all_items`
- `unemployment_rate`
- `federal_funds_rate`
- `nonfarm_payrolls`

### Trends features

- `trends_walmart`
- `trends_grocery_store`
- `trends_discount_store`
- `trends_cleaning_supplies`

These features were engineered and made available in the curated warehouse layer, and they remain valuable platform assets for analysis and future experimentation.

## Why the production feature set stayed with the baseline

The production path stayed with `calendar_lag_rolling_baseline` because it performed better than the wider variants in the project’s model evaluation workflow.

The key practical outcome was:

- adding the external feature groups did not improve the target prediction enough
- in the tested runs, the broader feature sets reduced model performance rather than improving it
- the strongest predictive signal came from the series’ own temporal structure rather than the added external drivers

In plain terms, the sales signal in this M5 demand setup was driven more by:

- recent sales history
- short-, weekly-, and monthly-like recurrence
- calendar position

than by the external variables added in the broader experiments.

## What that means for this retail forecasting problem

This result is meaningful for the current project.

It suggests that, for this dataset and this forecasting setup:

- the target series already carries a strong autoregressive signal
- calendar structure explains a large share of the predictable movement
- the added weather, macro, and trends variables were not strong direct drivers of daily unit sales at the level used in this model
- increasing feature breadth did not automatically increase forecasting quality

That does not mean those external sources are useless. It means they were not strong enough predictors for the implemented production objective to justify replacing the simpler and better-performing baseline.

## Why this is the right production choice

Using `calendar_lag_rolling_baseline` in production gives the platform:

- the best observed model performance from the implemented experiments
- a simpler and more stable feature contract
- lower operational complexity
- clearer training and inference parity
- easier debugging when batch forecasts need investigation

That is why the production training configuration and the production prediction configuration both use:

- `feature_set_name = "calendar_lag_rolling_baseline"`

## Validation approach behind the choice

The production model decision was made through the project’s rolling backtest workflow.

The implemented validation path uses:

- a 28-day forecast horizon
- 5 rolling windows
- consistent evaluation metrics including WMAPE, MAE, and RMSE

 


## Scheduling

The implemented production schedules are:

- training extract export and training: weekly on Monday at 02:00 London time
- batch prediction: daily at 04:00 London time

This operating model keeps the rolling 28-day forecast horizon refreshed daily without retraining more often than necessary.

## Runtime discovery from SSM

The ECS-based DAGs do not hardcode live infrastructure coordinates in the DAG body.

Instead, they resolve required runtime configuration from AWS Systems Manager Parameter Store at task runtime.

The DAGs resolve values such as:

- ECS cluster name
- MLflow tracking URI
- ECS task definition family
- private subnet IDs
- security group ID

This keeps the DAGs operationally clean and avoids parse-time AWS lookups.

## Shared ECS ML runtime

The production ML jobs run through the shared runtime container defined by the ML runtime image.

The runtime is used by the DAGs through container command overrides.

The main production commands are:

- `export-training-extract`
- `train-lightgbm`
- `predict-next-28-days`

This design keeps the orchestration layer thin and keeps the compute logic in the runtime image.

## MLflow role in the platform

MLflow is the system of record for ML run metadata and model registration state.

In the production workflow, MLflow is used to:

- record training runs
- store artifacts
- track model versions
- provide the latest trained model for prediction workflows

The prediction step depends on this model tracking and registration path.

## Forecast writeback

Prediction outputs are written back to the warehouse.

This step is operationally important because it makes the forecast outputs available to downstream consumers without requiring them to read directly from ML runtime artifacts.

The forecast writeback is the bridge between the ML platform and the downstream application-serving layer.

## Monitoring outputs

After forecast writeback, monitoring is exposed through warehouse-native views.

The implemented monitoring outputs include:

- forecast run monitoring
- latest forecast freshness

These views allow the platform to answer operational questions such as:

- when forecasts were last generated
- which model version produced them
- whether the forecast horizon is fresh
- whether forecast outputs are complete enough for downstream use

## Local developer workflow

For local ML platform work, use the main runtime environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
````

The main local workflow areas are:

* training extract logic
* training logic
* inference logic
* MLflow integration
* writeback logic

The most relevant repository areas are:

* `training/`
* `training/data_extract/`
* `training/models/`
* `training/prediction/`
* `training/utils/`
* `training/settings/`
* `training/runtime_cli.py`
* `orchestration/airflow/dags/20_export_training_extract_ecs.py`
* `orchestration/airflow/dags/21_train_lightgbm_ecs.py`
* `orchestration/airflow/dags/22_predict_next_28_days_ecs.py`

## Running the ML platform through MWAA

MWAA is private and must be accessed through the tunnel pattern.

For macOS:

```bash
make connect-mwaa-mac
```

For other operating systems:

```bash
make connect-mwaa
```

Once the tunnel is open, use the MWAA / Airflow UI to trigger the ML DAGs in this order:

1. `20_export_training_extract_ecs`
2. `21_train_lightgbm_ecs`
3. `22_predict_next_28_days_ecs`

That is the correct operational order for the production ML workflow.

## Runtime image deployment

The ECS ML runtime depends on the production ML runtime image existing in ECR.

Build and push the runtime image from the project root with:

```bash
make mlops-ci-push-ml-runtime
```

After the image is pushed, make sure the ECS ML stack points to the correct runtime image in:

```text
infra/terraform/envs/prod/ecs-ml/terraform.tfvars
```

The ECS stack should only create the task definition after the runtime image exists.

Then apply the ECS ML stack again:

```bash
cd infra/terraform/envs/prod
make apply-ecs-ml
```

## MLflow image deployment

The MLflow service image is also pushed from the project root.

Build and push it with:

```bash
make docker-push-mlflow
```

This keeps the MLflow service image aligned with the production infrastructure.






## ML image CI/CD pipeline

The ML platform has a separate image deployment path for its production containers.

The GitHub Actions workflow is:

- `.github/workflows/prod-deploy-ml-images.yml`

This workflow is a manual production deployment path for container images.

### What it deploys

It supports two image targets:

- `ml-runtime`
- `mlflow`

The runtime image is used by ECS batch jobs for:

- training extract export
- model training
- retraining
- batch inference

The MLflow image is used by the MLflow service deployment path.

### How the workflow is designed

The workflow is:

- manual trigger only
- bound to the GitHub `prod` environment
- authenticated through GitHub OIDC
- configured to assume the AWS deploy role from GitHub
- designed to prevent overlapping production image deploys

For `ml-runtime`, the workflow uses the caller-provided image tag.

For `mlflow`, the workflow uses the Makefile-managed MLflow tag.

### How to use it

In GitHub:

1. open the repository
2. go to `Actions`
3. open `Prod - Deploy ML Images (manual)`
4. click `Run workflow`
5. choose the `image_target`
6. if deploying `ml-runtime`, provide the `image_tag`
7. run the workflow against the intended branch

### Runtime behavior of the workflow

When the selected target is `ml-runtime`, the workflow runs:

```bash
make mlops-ci-push-ml-runtime
````

When the selected target is `mlflow`, the workflow runs:

```bash
make mlops-ci-push-mlflow
```

This keeps image publishing explicit, reviewable, and separated from normal code pushes.

### Operational follow-up after image publishing

After publishing a new ML runtime image, the ECS ML stack must point to the correct runtime image URI and tag in:

* `infra/terraform/envs/prod/ecs-ml/terraform.tfvars`

Then the ECS ML stack should be reapplied so the task definition uses the newly published image.

If the MLflow image changed and the service deployment depends on the new tag, the relevant infrastructure or service update should also be applied so the live environment uses that image.



## MWAA deployment dependency

The ML platform depends on MWAA not only existing as infrastructure, but also having the correct deployment artifacts uploaded.

The relevant project commands include:

```bash
make mwaa-upload-all
make mwaa-build-wheel
make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
```

After runtime or orchestration changes, apply MWAA again if needed so the production environment uses the correct artifacts and runtime references.

## Data-platform dependency

The ML platform depends on the data platform completing successfully first.

The ML DAGs should only be run after the full data-platform DAG has produced the curated Gold warehouse outputs needed by the ML extract and training pipeline.

That means the operational order is:

1. run the data platform
2. run training extract export
3. run model training
4. run prediction
5. verify forecast writeback and monitoring
6. proceed to snapshot export if needed

## Relationship to the forecast application

The ML platform ends when forecasts and monitoring outputs are available in the warehouse.

The forecast application layer begins after that, when snapshot export reads those warehouse outputs and publishes the latest application snapshot.

## Related documents

- [README.md](../README.md)
- [infrastructure](./infrastructure.md)
- [data platform](./data-platform.md)



