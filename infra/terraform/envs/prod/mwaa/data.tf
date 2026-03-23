# ------------------------------------------------------------------------------
# Pull latest S3 VersionId for optional MWAA artifacts (requirements/plugins/startup)
# ------------------------------------------------------------------------------

data "aws_s3_object" "requirements" {
  count  = var.requirements_s3_path == null ? 0 : 1
  bucket = data.terraform_remote_state.s3.outputs.airflow_bucket_name
  key    = var.requirements_s3_path
}

data "aws_s3_object" "plugins" {
  count  = var.plugins_s3_path == null ? 0 : 1
  bucket = data.terraform_remote_state.s3.outputs.airflow_bucket_name
  key    = var.plugins_s3_path
}

data "aws_s3_object" "startup" {
  count  = var.startup_script_s3_path == null ? 0 : 1
  bucket = data.terraform_remote_state.s3.outputs.airflow_bucket_name
  key    = var.startup_script_s3_path
}