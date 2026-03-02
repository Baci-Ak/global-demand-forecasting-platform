# ==============================================================================
# envs/dev/monitoring/outputs.tf
# ==============================================================================
#
# Purpose
# - Expose key monitoring resources so operators/scripts can reference them without
#   guessing names.
# ==============================================================================

output "alerts_sns_topic_arn" {
  description = "Central SNS topic ARN for all infrastructure alerts."
  value       = aws_sns_topic.alerts.arn
}

# ------------------------------------------------------------------------------
# RDS alarms
# ------------------------------------------------------------------------------

output "rds_alarm_names" {
  description = "CloudWatch alarm names for RDS Postgres."
  value = [
    aws_cloudwatch_metric_alarm.rds_cpu_high.alarm_name,
    aws_cloudwatch_metric_alarm.rds_free_storage_low.alarm_name,
    aws_cloudwatch_metric_alarm.rds_connections_high.alarm_name,
    aws_cloudwatch_metric_alarm.rds_freeable_memory_low.alarm_name,
    aws_cloudwatch_metric_alarm.rds_disk_queue_depth_high.alarm_name,
  ]
}

# ------------------------------------------------------------------------------
# Redshift Serverless alarms
# ------------------------------------------------------------------------------

output "redshift_alarm_names" {
  description = "CloudWatch alarm names for Redshift Serverless."
  value = [
    aws_cloudwatch_metric_alarm.redshift_compute_capacity_high.alarm_name,
    aws_cloudwatch_metric_alarm.redshift_database_connections_high.alarm_name,
  ]
}