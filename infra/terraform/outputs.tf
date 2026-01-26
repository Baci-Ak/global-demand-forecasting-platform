/*
  File: outputs.tf

  Purpose:
  - Export useful values after apply (e.g., bucket names, ARNs).
  - Keep this file even if initially empty; we will add outputs as resources are added.
*/


output "bronze_bucket_name" {
  description = "Bronze bucket name for the active environment."
  value       = module.bronze_bucket.bucket_name
}
