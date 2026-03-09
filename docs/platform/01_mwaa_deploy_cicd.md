
# MWAA Deploy CI/CD

## Purpose

Document how MWAA deployments work in this project for both **dev** and **prod**.

This is important because uploading artifacts to S3 is **not enough** for full MWAA runtime changes in this repository. Runtime changes must go through **Terraform apply** on the MWAA stack so the environment actually picks up the latest registered artifacts.

---

## Deployment modes

Both dev and prod MWAA deploy workflows support two modes:

### `dags-only`
Use when only DAG Python files changed.

What it does:
- sync DAGs to the MWAA S3 DAG prefix

What it does **not** do:
- no Terraform apply
- no runtime refresh
- no startup / requirements / plugins / wheel refresh

Use this for:
- DAG logic changes
- task dependency changes
- schedule changes
- comments / documentation inside DAG files

---

### `full`
Use when any MWAA runtime artifact changed.

What it does:
- uploads DAGs
- uploads requirements
- uploads plugins
- uploads startup artifacts
- builds and uploads the application wheel
- runs `terraform apply` on the MWAA stack

Why this is required:
- in this project, Terraform is the source of truth for the MWAA environment
- runtime changes are not reliably picked up just by uploading files to S3
- `startup.sh`, `requirements.txt`, `plugins.zip`, and wheel bootstrap behavior must go through Terraform-managed MWAA refresh

Use this for:
- `orchestration/airflow/startup/startup.sh`
- `orchestration/airflow/startup/gdf_runtime.conf`
- `docker/airflow/requirements-mwaa.txt`
- `orchestration/airflow/plugins/*`
- Python package / wheel changes
- changes that affect worker runtime behavior

---

## GitHub Actions workflows

### Dev
- Workflow: `Dev - Deploy to MWAA (manual)`
- Environment: `dev`

### Prod
- Workflow: `Prod - Deploy to MWAA (manual)`
- Environment: `prod`

Both workflows are:
- manual only
- OIDC-based
- environment-scoped
- split into `dags-only` and `full`

---

## Terraform apply behavior

### Dev full deploy
Runs:

```bash
cd infra/terraform/envs/dev
make apply-mwaa
````

### Prod full deploy

Runs:

```bash
cd infra/terraform/envs/prod
make apply-mwaa
```

This is the critical step that makes MWAA pick up runtime changes.

---

## Operational rule of thumb

Use:

* `dags-only` for DAG code only
* `full` for anything that changes MWAA runtime behavior

When unsure, use **`full`**.

---

## Important note on wheel updates

The wheel is uploaded to S3, but MWAA workers only pick it up when the startup/bootstrap path is refreshed. That is why wheel-related deploys must use **`full`**.

---

## Important note on startup config

`gdf_runtime.conf` is downloaded by `startup.sh` at runtime. Updating the file in S3 alone is not sufficient if MWAA does not actually rerun the updated startup flow. That is another reason `full` must go through Terraform apply.

---

## Summary

### Safe mapping

#### `dags-only`

* DAG files only

#### `full`

* startup changes
* runtime config changes
* requirements changes
* plugins changes
* wheel / package changes
* anything affecting worker bootstrap or runtime

