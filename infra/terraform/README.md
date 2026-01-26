# Terraform Infrastructure (GDF)

Purpose
- This folder contains Infrastructure-as-Code (IaC) for the Global Demand Forecasting platform.
- We start with a small, production-grade skeleton and iterate safely.

How to use (dev)
1) cd infra/terraform/env/dev
2) terraform init
3) terraform plan -var-file=terraform.tfvars
4) terraform apply -var-file=terraform.tfvars

Notes
- Do NOT commit secrets. Use `terraform.tfvars` locally and keep an `*.example` template in git.
- Each environment (dev/prod) has its own folder under `env/`.
