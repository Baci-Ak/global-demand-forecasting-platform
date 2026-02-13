# ==============================================================================
# modules/mwaa/log_groups.tf
# ==============================================================================
#
# Purpose
# - Manage MWAA CloudWatch Log Groups explicitly so retention is enforced.
#
# Why this matters
# - MWAA creates log streams continuously (every task run, scheduler activity, etc.).
# - Without retention, log storage grows indefinitely and costs accumulate.
# - Managing log groups here keeps retention environment-driven (dev/prod) and
#   prevents manual console drift.
#
# Notes
# - MWAA log group names are deterministic:
#   airflow-<environment-name>-<component>
# - We create them up-front so retention applies immediately.
# ==============================================================================

locals {
  mwaa_log_groups = {
    dag_processing = "airflow-${local.name_prefix}-DAGProcessing"
    scheduler      = "airflow-${local.name_prefix}-Scheduler"
    webserver      = "airflow-${local.name_prefix}-WebServer"
    worker         = "airflow-${local.name_prefix}-Worker"
    task           = "airflow-${local.name_prefix}-Task"
  }
}

resource "aws_cloudwatch_log_group" "mwaa" {
  for_each = local.mwaa_log_groups

  name              = each.value
  retention_in_days = var.cloudwatch_log_retention_days

  tags = merge(
    { Name = each.value },
    var.tags
  )
}
