output "ml_ecr_repository_url" {
  description = "ECR repository URL for ML runtime images."
  value       = module.ml_ecr.repository_url
}