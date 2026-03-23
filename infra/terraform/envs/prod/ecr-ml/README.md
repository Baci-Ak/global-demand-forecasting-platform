# prod/ecr-ml

Purpose:
- provision the production ECR repository for ML runtime images

Managed resources:
- ECR repository: `gdf-prod-ml-runtime`

Notes:
- Terraform-managed only
- consumed by future CI/CD image push workflow
- repository URL is exported as a Terraform output and published to SSM by the monitoring stack