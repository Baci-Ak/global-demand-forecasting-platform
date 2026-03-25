# Infrastructure

This document describes the infrastructure of the Global Demand Forecasting Platform.

It covers the infrastructure-as-code approach, Terraform layout, production stack structure, AWS services, networking model, secrets model, access model, and the deployment workflow used to provision and update the platform.

This is the main infrastructure reference for the project.

## Infrastructure approach

The platform infrastructure is managed as code with Terraform.

Infrastructure is not deployed from a single monolithic root module. It is split into environment-specific stacks with shared reusable modules. This makes the platform easier to provision, update, troubleshoot, and evolve without coupling every service into one large Terraform apply.

The infrastructure code lives under:

```text
infra/terraform/
````

The main parts are:

* `bin/` for helper scripts
* `bootstrap/` for Terraform backend bootstrap
* `envs/` for environment-specific stacks
* `modules/` for reusable Terraform building blocks

## What the infrastructure provides

The infrastructure supports the full production platform, including:

* the private network foundation
* the S3-based data lake and deployment artifact storage
* the Redshift warehouse
* the RDS Postgres operational metadata database
* the MWAA orchestration environment
* the ECS batch ML runtime
* the MLflow service
* the ECR image registry
* the IAM and OIDC access model
* the tunnel-based developer access pattern

The infrastructure exists to make the platform services available, connected, secure, and operable.

## Infrastructure-as-code structure

## `infra/terraform/bin/`

This directory contains helper scripts used for connectivity and maintenance.

It includes:

* `connect_dev.sh`
* `gdf-dev-connect-mwaa-mac.sh`
* `tunnel_mwaa_ui.sh`
* `tunnel_rds_audit.sh`
* `tunnel_redshift.sh`
* `update_tf_backend_references.sh`

These scripts support local access to private services and backend-related maintenance tasks.

## `infra/terraform/bootstrap/`

This directory bootstraps the Terraform remote state backend.

It provisions the infrastructure needed for Terraform itself, including the remote state storage pattern used by the rest of the platform.

The repository contains:

* `bootstrap/tfstate/`
* `bootstrap/tfstate-prod/`

These bootstrap paths provide the backend foundation before the environment stacks are applied.

## `infra/terraform/envs/`

This directory contains the environment-specific infrastructure stacks.

The repository contains:

* `infra/terraform/envs/dev/`
* `infra/terraform/envs/prod/`

Each environment is split into multiple stacks rather than one root apply. That stack split is part of the operating model of the platform.

## `infra/terraform/modules/`

This directory contains the reusable Terraform modules used by the environment stacks.

The current module set includes:

* `ci-federated-role`
* `ecr`
* `ecs-ml-runtime`
* `mlflow-ecs-service`
* `mwaa`
* `network`
* `rds-postgres`
* `redshift-serverless`
* `s3`
* `vpc_endpoints`

These modules define the reusable service building blocks that are composed into the dev and prod environments.

## Environment stack design

The production environment is managed as separate Terraform stacks.

The production stacks are:

* `iam`
* `network`
* `ssm-jumphost`
* `s3`
* `rds-postgres`
* `redshift`
* `ecr-ml`
* `ecs-ml`
* `mlflow`
* `mwaa`
* `monitoring`

This stack split matters because the platform has real dependencies between services. The infrastructure is intentionally provisioned in dependency order.

## Core infrastructure services

## IAM

The IAM stack defines the access model for the platform.

It includes:

* engineer access configuration
* tunnel-related policies
* CI/CD access configuration
* GitHub OIDC provider configuration in production
* roles and policy attachments required by infrastructure and deployment workflows

IAM is the foundation of who can provision, update, connect to, and deploy into the platform.

## Network

The network stack creates the private AWS network foundation for the platform.

It includes:

* the VPC
* subnets
* route configuration
* workload security groups
* workload security group rules

The network design supports private workloads and controlled service-to-service connectivity across the platform.

## SSM jumphost

The SSM jumphost stack provides the access bridge used for the platform’s private connectivity model.

It includes:

* the instance definition
* IAM configuration for SSM access
* security configuration

This service is what makes local tunnel-based access possible for private platform services.

Without this access path, local developer connectivity to Redshift, RDS Postgres, MWAA, and MLflow would not work in the current design.

## S3

S3 is the platform object storage foundation and data lake layer.

It is used for several important platform responsibilities:

* Bronze raw data landing
* MWAA deployment artifacts
* MLflow artifact storage
* forecast application snapshot storage
* general platform object storage needs

For the data platform specifically, S3 acts as the raw landing and persistence layer for source data before warehouse loading. In that sense, S3 is the platform data lake.

For the orchestration and ML layers, S3 also acts as the storage layer for packaged assets, artifacts, and snapshot exports.


## RDS Postgres

The RDS Postgres stack provisions the operational metadata database.

This service stores:

* ingestion audit metadata
* data quality audit metadata
* MLflow metadata

This database is separate from Redshift on purpose. It supports operational traceability and ML system state without mixing that metadata into the warehouse itself.

RDS Postgres is private and is accessed locally through the tunnel pattern.

Secrets for the database are created in AWS and stored in Secrets Manager.

## Redshift

The Redshift stack provisions the warehouse used by the platform.

It supports:

* staging loads
* Silver and Gold transformations through dbt
* ML-ready warehouse datasets
* forecast writeback
* warehouse monitoring views

Redshift is the core analytical and ML-ready warehouse layer of the platform.

It is private and accessed locally through the tunnel pattern.

Connection details are stored in AWS Secrets Manager.

## ECR

The ECR stack provisions the container registry used by the ML platform.

It provides the registry location for:

* the ECS ML runtime image
* the MLflow image

The registry must exist before those images can be pushed and used by downstream runtime services.

## ECS ML runtime

The ECS ML stack provisions the batch runtime used by the ML platform.

It is used for:

* training extract jobs
* model training jobs
* batch inference jobs

This runtime is image-driven, which means the final ECS task definition depends on a real image already being present in ECR.

Because of that dependency, the ECS ML runtime follows a staged deployment flow rather than a one-pass apply from the beginning.

## MLflow

The MLflow stack provisions the hosted MLflow service used in the production platform.

MLflow supports:

* experiment tracking
* model registry
* artifact integration with S3
* metadata persistence in RDS Postgres

MLflow is part of the production platform infrastructure. It is not treated as a local-only development tool.

## MWAA

The MWAA stack provisions the Airflow orchestration environment for the platform.

MWAA orchestrates:

* the full data platform refresh
* training extract export
* model training
* batch prediction

MWAA depends on both infrastructure and deployment artifacts. The environment itself may exist, but it is only operationally useful after the required DAGs, plugins, startup files, requirements, and project wheel have been uploaded to the MWAA artifact bucket.

## Monitoring

The monitoring stack provisions supporting monitoring and parameter infrastructure used by the platform.

This includes monitoring-related resources and shared runtime parameters that support the operating environment.


## Networking and access model

The infrastructure is designed around private access for core platform services.

This applies to:

- Redshift
- RDS Postgres
- MWAA
- MLflow

These services are not intended to be accessed directly from a developer laptop through public endpoints.

Instead, developer access follows the tunnel-based pattern implemented by the helper scripts in `infra/terraform/bin/` and surfaced through the root `Makefile`.

Typical commands include:

- `make connect-redshift`
- `make connect-postgres`
- `make connect-mwaa`
- `make connect-mwaa-mac`
- `make connect-mlflow`

## Engineer access prerequisite

Before a developer can use the tunnel-based access workflow, that user must be granted the correct AWS access.

In production, this means the user must be added to the AWS IAM user group:

- `gdf-prod-engineer`

This is done in AWS through:

- IAM
- User groups
- `gdf-prod-engineer`
- Add users

Without the required group membership and policies, the tunnel-based commands will not work correctly.

## Local access behavior

Once the tunnel is open, local tools should connect through `localhost` rather than the private AWS hostname.

This is especially important for database clients such as DBeaver and for private service access from a local machine.

The tunnel must remain open while the local client session is active.



## Secrets and configuration model

Infrastructure-created credentials and connection details are stored in AWS.

The main configuration stores used by the platform are:

* AWS Secrets Manager
* AWS Systems Manager Parameter Store

### Secrets Manager

Secrets Manager stores connection and credential material for platform services.

Examples include warehouse and database credentials.

For local connections to private services, developers should use Secrets Manager as the source of truth for:

* usernames
* passwords
* database names
* ports
* service endpoints

Even when the real service endpoint is stored in the secret, local clients still connect through the tunnel endpoint on `localhost`.

### Parameter Store

Parameter Store is used for environment configuration that needs to be resolved by scripts, runtime code, and deployment processes.

It supports the operational configuration layer of the platform.

## External source secrets and API setup

The infrastructure and runtime also rely on external source credentials for some ingestion paths.

These need to be available for the source ingestion code and orchestration workflows to succeed.

The important external source secrets are:

* Kaggle credentials
* FRED API key

These should be stored in AWS Secrets Manager for the production environment.

For example, the production setup should include plaintext secrets such as:

* `gdf/prod/kaggle_credentials`
* `gdf/prod/fred_api_key`

These external source credentials are part of the deployable platform setup, not just a local developer concern, because ingestion workflows depend on them.

## Provisioning model

Production infrastructure is orchestrated from:

```text
infra/terraform/envs/prod/Makefile
```

The production apply order is:

1. `iam`
2. `network`
3. `ssm-jumphost`
4. `s3`
5. `rds-postgres`
6. `redshift`
7. `ecr-ml`
8. `ecs-ml`
9. `mlflow`
10. `mwaa`
11. `monitoring`

This order reflects real service dependencies and should be preserved.

## Deployment workflow

When provisioning or rebuilding the environment, the practical deployment sequence is:

1. configure AWS credentials and local environment values
2. provision the infrastructure stacks
3. publish the required runtime images
4. update the ECS ML runtime stack to reference the real published image
5. apply the ECS ML runtime stack again
6. upload MWAA deployment artifacts
7. apply or refresh MWAA so orchestration uses the live runtime and artifact set
8. confirm the environment is converged

This is the real operating workflow for the platform infrastructure.

## Staged ECS ML runtime deployment

The ECS ML runtime cannot be fully deployed before the runtime image exists in ECR.

That is why the ECS stack uses a staged apply model through:

```text
infra/terraform/envs/prod/ecs-ml/terraform.tfvars
```

In practice, the flow is:

* provision the ECR registry and supporting infrastructure first
* build and push the ML runtime image
* update the ECS stack to use the published image URI and tag
* apply the ECS stack again so the task definition points at a valid image

This pattern is part of the deployment design and should be documented explicitly because it affects infrastructure setup and change management.

## MWAA deployment readiness

MWAA depends on both infrastructure and packaged deployment artifacts.

The Airflow environment requires the following artifacts to be available in the MWAA S3 bucket:

* DAGs
* plugins
* requirements
* startup files
* packaged project wheel

This means there is an important difference between:

* the MWAA infrastructure existing
* the MWAA environment being ready to run the platform

Both conditions matter.

















## Setup and update workflow

This section is the operational runbook for setting up, updating, and tearing down the infrastructure.

Follow it in order.

## 1. Install the required local tools

Install these tools on your machine before doing any infrastructure work:

- AWS CLI v2
- Terraform
- Git
- Make
- Docker

Use the official AWS CLI installation guide here:

- [AWS CLI v2 installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

Use the official AWS CLI configuration guide here:

- [AWS CLI configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

Use the official Terraform installation guide here:

- [Terraform installation guide](https://developer.hashicorp.com/terraform/install)

## 2. Configure AWS access locally

After AWS CLI is installed, configure your local terminal access with:

```bash
aws configure
````

Configure:

* AWS Access Key ID
* AWS Secret Access Key
* default region, usually `us-east-1`
* default output format

## 3. Create and populate the local `.env` file

Create the local environment file from the repository example:

```bash
cp .env.example .env
```

For local developer workflows in this repository, set the AWS credentials in `.env` as well:

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
```

This repository also expects environment-based configuration for warehouse access, Postgres access, MLflow, snapshot export, and related runtime settings.

## 4. Bootstrap the Terraform remote state first

Before applying the production environment stacks, bootstrap the Terraform backend first.

Start in:

```bash
cd infra/terraform/bootstrap/tfstate-prod
```

Then run:

```bash
terraform init
terraform plan
terraform apply
```

This step creates the remote state foundation used by the production stacks.

Do this before working in:

```text
infra/terraform/envs/prod/
```

## 5. Review the production stack order

The production environment is applied in dependency order from:

```text
infra/terraform/envs/prod/Makefile
```

The production stack order is:

1. `iam`
2. `network`
3. `ssm-jumphost`
4. `s3`
5. `rds-postgres`
6. `redshift`
7. `ecr-ml`
8. `ecs-ml`
9. `mlflow`
10. `mwaa`
11. `monitoring`

This order matters and should be preserved.

## 6. Prepare the ECS ML stack for the first infrastructure apply

Before the ML runtime image exists in ECR, update this file:

```text
infra/terraform/envs/prod/ecs-ml/terraform.tfvars
```

In the runtime image section, temporarily disable task definition creation before the first full apply.

Use this form before the image exists:

```tfvars
# ------------------------------------------------------------------------------
# Runtime image
# ------------------------------------------------------------------------------

create_task_definition = false

# set these two values when the runtime image is in ECR repository
# create_task_definition = true
# ml_runtime_image       = "697980229152.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-ml-runtime:latest"
```

This prevents the ECS ML stack from trying to create a task definition before the runtime image has been built and pushed.

## 7. Run the first production infrastructure apply

Move into the production environment directory:

```bash
cd infra/terraform/envs/prod
```

Preview the environment:

```bash
make plan-all
```

Apply the environment:

```bash
make apply-all
```

At this stage, the platform infrastructure should exist, including the ECR repository, but the ECS ML task definition should still be disabled until the runtime image exists.

## 8. Build and push the required runtime images

Return to the project root:

```bash
cd ../../..
```

Build and push the production ML runtime image:

```bash
make mlops-ci-push-ml-runtime
```

Build and push the MLflow image:

```bash
make docker-push-mlflow
```

These commands publish the required images into the Terraform-managed ECR repository.

## 9. Re-enable the ECS ML task definition after the runtime image exists

After the ML runtime image has been pushed successfully, go back to:

```text
infra/terraform/envs/prod/ecs-ml/terraform.tfvars
```

Update the runtime image section so it points at the real published image and enables task definition creation again.

Use this form after the image exists:

```tfvars
# ------------------------------------------------------------------------------
# Runtime image
# ------------------------------------------------------------------------------

# create_task_definition = false

# set these two values when the runtime image is in ECR repository
create_task_definition = true
ml_runtime_image       = "798329741238.dkr.ecr.us-east-1.amazonaws.com/gdf-prod-ml-runtime:latest"
```

Use the actual repository URI and tag that were pushed for your environment.

## 10. Apply the ECS ML stack again

After updating `ecs-ml/terraform.tfvars`, apply the ECS ML stack again:

```bash
cd infra/terraform/envs/prod
make apply-ecs-ml
```

This is the apply that creates or refreshes the ECS ML task definition against the real published runtime image.

## 11. Upload MWAA deployment artifacts

Return to the project root and upload the Airflow deployment artifacts:

```bash
cd ../../..
make mwaa-upload-all
make mwaa-build-wheel
make mwaa-upload-wheel WHEEL=dist/gdf-0.1.0-py3-none-any.whl
```

If the wheel filename differs, use the actual wheel present in `dist/`.

These uploads are required because MWAA depends on the deployment artifacts as well as the infrastructure itself.

## 12. Apply MWAA again after the runtime and artifacts are ready

After the runtime image exists and the MWAA artifacts have been uploaded, apply MWAA again:

```bash
cd infra/terraform/envs/prod
make apply-mwaa
```

This aligns the orchestration environment with the live runtime and uploaded artifact set.

## 13. Confirm the environment is converged

Run a final full plan:

```bash
make plan-all
```

The goal is to confirm there are no unexpected infrastructure changes left to apply.

## 14. Typical update workflow

For normal infrastructure and runtime updates after the platform already exists, the common workflow is:

1. update Terraform, configuration, image, or MWAA artifacts as needed
2. run `make plan-all`
3. apply only the affected stack where possible
4. push updated runtime images if the ML runtime changed
5. reapply `ecs-ml` if the runtime image reference changed
6. upload MWAA artifacts if DAGs, plugins, startup files, requirements, or the project wheel changed
7. reapply `mwaa` if the orchestration environment needs to pick up those changes
8. run `make plan-all` again to confirm convergence

## 15. Service access after deployment

Once the infrastructure is live, use the tunnel pattern for private service access:

```bash
make connect-redshift
make connect-postgres
make connect-mwaa
make connect-mlflow
```

For macOS MWAA access:

```bash
make connect-mwaa-mac
```

After the tunnel is open, connect local tools through `localhost`, not the private AWS hostname stored in the secret.

## 16. Destroy workflow

When a full teardown is required, use the production Terraform orchestration Makefile from:

```text
infra/terraform/envs/prod/
```

Destroy all stacks in reverse dependency order with:

```bash
make destroy-all
```

Use targeted destroy commands only when you intentionally want to remove a specific stack and understand the dependency implications.

Do not destroy the production backend bootstrap resources casually. The backend under `infra/terraform/bootstrap/tfstate-prod/` is the state foundation for the environment and should be treated separately from routine stack teardown.

## 17. Operational notes

A few rules matter in practice:

* bootstrap remote state before the environment stacks
* do not enable ECS task definition creation before the runtime image exists
* do not expect MWAA to be operational before its deployment artifacts are uploaded
* do not connect directly to private service endpoints from a laptop
* always finish with a fresh `make plan-all` to confirm the environment is clean

## Related documents

- [README.md](../README.md)
- [infrastructure](./ml-platform.md)
- [data platform](./data-platform.md)
- [data platform](./developer-quickstart.md)