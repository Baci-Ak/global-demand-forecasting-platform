# GitHub Actions OIDC IAM Roles

## Purpose

Document how GitHub Actions assumes AWS roles in this project, and how those roles are now managed by Terraform instead of manually in the AWS console.

---

## Managed roles

This project uses one GitHub Actions federated IAM role per environment:

- `gdf-dev-github-actions`
- `gdf-prod-github-actions`

These roles are now managed by Terraform via:

- `infra/terraform/modules/ci-federated-role`
- `infra/terraform/envs/dev/iam`
- `infra/terraform/envs/prod/iam`

---

## Why this matters

Previously, these roles were created manually in AWS.

That was not ideal because:
- engineers had to click around in AWS
- trust relationships and policies could drift
- onboarding and environment recreation were less reliable

Now the roles are managed as code.

---

## Trust policy design

The federated trust policy is parameterized through Terraform inputs:

- OIDC provider ARN
- OIDC audience
- GitHub repo owner
- GitHub repo name
- GitHub environment name

This means future changes to:
- repository
- organization
- GitHub environment name
- OIDC configuration

can be handled through Terraform variables instead of manual console edits.

---

## Current GitHub OIDC pattern

The roles currently trust:

- OIDC provider: `token.actions.githubusercontent.com`
- audience: `sts.amazonaws.com`

Subject pattern:

### Dev
`repo:Baci-Ak/global-demand-forecasting:environment:dev`

### Prod
`repo:Baci-Ak/global-demand-forecasting:environment:prod`

---

## What permissions these roles need

These CI/CD roles are used for MWAA deployment workflows and Terraform apply for the MWAA stack.

They include permissions for:
- Terraform lock table access in DynamoDB
- MWAA environment update/apply operations
- IAM read/write for the MWAA execution role
- CloudWatch Logs read/manage for MWAA log groups
- EC2 security group read/manage needed by the MWAA stack

They are separate from:
- the MWAA execution role
- engineer human IAM access
- other application/runtime permissions

---

## Operational model

### Dev
Terraform stack:
- `infra/terraform/envs/dev/iam`

Role output:
- `github_actions_role_arn`

### Prod
Terraform stack:
- `infra/terraform/envs/prod/iam`

Role output:
- `github_actions_role_arn`

---

## GitHub Actions usage

GitHub Actions workflows use environment-scoped secrets:

### Dev
- environment: `dev`
- secret: `AWS_ROLE_ARN`

### Prod
- environment: `prod`
- secret: `AWS_ROLE_ARN`

Those secrets should point to the Terraform-managed role ARNs.

---

## Important rule

Do not manually edit these IAM roles in AWS unless there is an emergency.

Permanent changes must be made in Terraform so the roles remain reproducible and consistent across engineers and environments.