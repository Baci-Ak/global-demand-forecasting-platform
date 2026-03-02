# ==============================================================================
# envs/dev/monitoring/ssm_params.tf
# ==============================================================================
#
# Purpose
# - Publish NON-SECRET connection coordinates to SSM Parameter Store so engineers
#   can run a single script (connect_dev.sh) without repo access.
#
# Stored values (non-secret):
# - jumphost instance id
# - MWAA webserver host
# - RDS endpoint host + port
# - Redshift endpoint host + port
# ==============================================================================

# --- MWAA webserver host ---
# output is like: https://<host>/
locals {
  ssm_base = "/gdf/${var.environment}"

  mwaa_webserver_host = trimsuffix(
    trimprefix(data.terraform_remote_state.mwaa.outputs.mwaa_webserver_url, "https://"),
    "/"
  )
}

resource "aws_ssm_parameter" "jumphost_instance_id" {
  name  = "${local.ssm_base}/ssm/jumphost_instance_id"
  type  = "String"
  value = data.terraform_remote_state.ssm_jumphost.outputs.jumphost_instance_id
  overwrite = true
}

resource "aws_ssm_parameter" "mwaa_webserver_host" {
  name  = "${local.ssm_base}/mwaa/webserver_host"
  type  = "String"
  value = local.mwaa_webserver_host
  overwrite = true
}

resource "aws_ssm_parameter" "rds_endpoint_host" {
  name  = "${local.ssm_base}/rds/endpoint_host"
  type  = "String"
  value = data.terraform_remote_state.rds.outputs.endpoint
  overwrite = true
}

resource "aws_ssm_parameter" "rds_port" {
  name  = "${local.ssm_base}/rds/port"
  type  = "String"
  value = tostring(data.terraform_remote_state.rds.outputs.port)
  overwrite = true
}

resource "aws_ssm_parameter" "redshift_endpoint_host" {
  name  = "${local.ssm_base}/redshift/endpoint_host"
  type  = "String"
  value = data.terraform_remote_state.redshift.outputs.endpoint
  overwrite = true
}

resource "aws_ssm_parameter" "redshift_port" {
  name  = "${local.ssm_base}/redshift/port"
  type  = "String"
  value = tostring(data.terraform_remote_state.redshift.outputs.port)
  overwrite = true
}