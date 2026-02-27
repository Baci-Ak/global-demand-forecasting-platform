# ==============================================================================
# modules/redshift-serverless/outputs.tf
# ==============================================================================
#
# Purpose
# - Export connection details for consumers.
# ==============================================================================

output "namespace_name" {
  description = "Redshift Serverless namespace name."
  value       = aws_redshiftserverless_namespace.this.namespace_name
}

output "workgroup_name" {
  description = "Redshift Serverless workgroup name."
  value       = aws_redshiftserverless_workgroup.this.workgroup_name
}

output "endpoint_address" {
  description = "Redshift Serverless endpoint address."
  value       = aws_redshiftserverless_workgroup.this.endpoint[0].address
}

output "endpoint_port" {
  description = "Redshift Serverless endpoint port."
  value       = aws_redshiftserverless_workgroup.this.endpoint[0].port
}

output "security_group_id" {
  description = "Security group id for Redshift."
  value       = aws_security_group.redshift.id
}


output "copy_role_arn" {
  description = "IAM role ARN that Redshift Serverless uses for COPY/UNLOAD to S3."
  value       = aws_iam_role.redshift_copy_role.arn
}