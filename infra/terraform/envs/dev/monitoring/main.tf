# ==============================================================================
# envs/dev/monitoring/main.tf
# ==============================================================================
#
# Purpose
# - Centralize monitoring + cost controls for the dev environment:
#   - One SNS topic for all alerts (email subscriptions)
#   - AWS Budgets monthly cost budget alerts
#   - CloudWatch alarms for core infrastructure (starting with RDS Postgres)
#
# Design
# - This stack reads identifiers from other stacks via terraform_remote_state.
# - Alarm sensitivity (periods/thresholds) is controlled via variables.tf/tfvars.
# - Keep resources grouped by service with clear section headers.
# ==============================================================================

# ------------------------------------------------------------------------------
# Remote state: RDS Postgres
# ------------------------------------------------------------------------------

data "terraform_remote_state" "rds" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/rds-postgres/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

# ------------------------------------------------------------------------------
# Remote state: Redshift
# ------------------------------------------------------------------------------

data "terraform_remote_state" "redshift" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/redshift/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}





# ------------------------------------------------------------------------------
# Remote state: SSM Jumphost
# ------------------------------------------------------------------------------

data "terraform_remote_state" "ssm_jumphost" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/ssm-jumphost/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

# ------------------------------------------------------------------------------
# Remote state: MWAA
# ------------------------------------------------------------------------------

data "terraform_remote_state" "mwaa" {
  backend = "s3"

  config = {
    bucket       = "gdf-dev-tfstate-f6df28"
    key          = "envs/dev/mwaa/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}







# ------------------------------------------------------------------------------
# Locals
# ------------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # CloudWatch RDS alarms require DBInstanceIdentifier.
  # rds-postgres stack exports `db_instance_identifier`.
  rds_instance_id = data.terraform_remote_state.rds.outputs.db_instance_identifier

  #cloudwatch redshift alarm
  redshift_workgroup_name = data.terraform_remote_state.redshift.outputs.workgroup_name
  redshift_namespace_name = data.terraform_remote_state.redshift.outputs.namespace_name


}

# ------------------------------------------------------------------------------
# Alerts: central SNS topic + email subscriptions
# ------------------------------------------------------------------------------

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  for_each = toset(var.alert_emails)

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

# ------------------------------------------------------------------------------
# Cost controls: AWS Budgets (monthly actual spend)
# ------------------------------------------------------------------------------

resource "aws_budgets_budget" "monthly_cost" {
  name         = "${local.name_prefix}-monthly-cost"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = var.budget_alert_thresholds_percent
    content {
      comparison_operator       = "GREATER_THAN"
      threshold                 = notification.value
      threshold_type            = "PERCENTAGE"
      notification_type         = "ACTUAL"
      subscriber_sns_topic_arns = [aws_sns_topic.alerts.arn]
    }
  }
}

# ------------------------------------------------------------------------------
# Alarms: RDS Postgres
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  alarm_description   = "RDS CPU utilization is high"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Average"
  threshold   = var.rds_cpu_high_threshold
  namespace   = "AWS/RDS"
  metric_name = "CPUUtilization"

  dimensions = {
    DBInstanceIdentifier = local.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage_low" {
  alarm_name          = "${local.name_prefix}-rds-free-storage-low"
  alarm_description   = "RDS free storage space is low"
  comparison_operator = "LessThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Minimum"
  threshold   = var.rds_free_storage_low_threshold_bytes
  namespace   = "AWS/RDS"
  metric_name = "FreeStorageSpace"

  dimensions = {
    DBInstanceIdentifier = local.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  alarm_name          = "${local.name_prefix}-rds-connections-high"
  alarm_description   = "RDS database connections are high"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Average"
  threshold   = var.rds_connections_high_threshold
  namespace   = "AWS/RDS"
  metric_name = "DatabaseConnections"

  dimensions = {
    DBInstanceIdentifier = local.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}





# ------------------------------------------------------------------------------
# Alarms: RDS Postgres (additional reliability signals)
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "rds_freeable_memory_low" {
  alarm_name          = "${local.name_prefix}-rds-freeable-memory-low"
  alarm_description   = "RDS freeable memory is low (risk of swapping / OOM)"
  comparison_operator = "LessThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Minimum"
  threshold   = var.rds_freeable_memory_low_threshold_bytes
  namespace   = "AWS/RDS"
  metric_name = "FreeableMemory"

  dimensions = {
    DBInstanceIdentifier = local.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_disk_queue_depth_high" {
  alarm_name          = "${local.name_prefix}-rds-disk-queue-depth-high"
  alarm_description   = "RDS disk queue depth is high (storage is saturated / IOPS constrained)"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Average"
  threshold   = var.rds_disk_queue_depth_high_threshold
  namespace   = "AWS/RDS"
  metric_name = "DiskQueueDepth"

  dimensions = {
    DBInstanceIdentifier = local.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}







# ------------------------------------------------------------------------------
# Alarms: Redshift Serverless (workgroup)
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "redshift_compute_capacity_high" {
  alarm_name          = "${local.name_prefix}-redshift-rrpu-high"
  alarm_description   = "Redshift Serverless compute usage (RPU utilization) is high"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Average"
  threshold   = var.redshift_rrpu_utilization_high_threshold
  namespace   = "AWS/RedshiftServerless"
  metric_name = "RPUUtilization"

  dimensions = {
    workgroupName = local.redshift_workgroup_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "redshift_database_connections_high" {
  alarm_name          = "${local.name_prefix}-redshift-connections-high"
  alarm_description   = "Redshift Serverless database connections are high"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  datapoints_to_alarm = var.alarm_datapoints_to_alarm

  statistic   = "Average"
  threshold   = var.redshift_connections_high_threshold
  namespace   = "AWS/RedshiftServerless"
  metric_name = "DatabaseConnections"

  dimensions = {
    workgroupName = local.redshift_workgroup_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}


