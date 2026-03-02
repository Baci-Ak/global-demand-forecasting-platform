
# ==============================================================================
# modules/mwaa/environment.tf
# ==============================================================================
#
# Purpose
# - Provision the Amazon MWAA environment.
#
# Scope
# - This file owns only the MWAA environment resource.
# - IAM, security groups, and locals are defined in their own files.
# ==============================================================================

resource "aws_mwaa_environment" "this" {
  name                  = local.name_prefix
  airflow_version       = var.airflow_version
  environment_class     = var.environment_class
  min_workers           = var.min_workers
  max_workers           = var.max_workers
  webserver_access_mode = var.webserver_access_mode

  execution_role_arn = aws_iam_role.mwaa_execution.arn

  source_bucket_arn = "arn:aws:s3:::${var.dag_s3_bucket}"
  dag_s3_path       = var.dag_s3_path

  # Optional artifacts (null means "not configured")
  requirements_s3_path   = var.requirements_s3_path
  plugins_s3_path        = var.plugins_s3_path
  startup_script_s3_path = var.startup_script_s3_path
  requirements_s3_object_version   = var.requirements_s3_object_version
  plugins_s3_object_version        = var.plugins_s3_object_version
  startup_script_s3_object_version = var.startup_script_s3_object_version

  airflow_configuration_options = var.airflow_configuration_options
  #environment_variables = var.environment_variables


  network_configuration {
    security_group_ids = concat([aws_security_group.mwaa.id], var.additional_security_group_ids)
    #security_group_ids = [aws_security_group.mwaa.id]
    subnet_ids         = var.private_subnet_ids
  }

  logging_configuration {
    dag_processing_logs {
      enabled   = var.logging_configuration.dag_processing.enabled
      log_level = var.logging_configuration.dag_processing.log_level
    }

    scheduler_logs {
      enabled   = var.logging_configuration.scheduler.enabled
      log_level = var.logging_configuration.scheduler.log_level
    }

    task_logs {
      enabled   = var.logging_configuration.task.enabled
      log_level = var.logging_configuration.task.log_level
    }

    webserver_logs {
      enabled   = var.logging_configuration.webserver.enabled
      log_level = var.logging_configuration.webserver.log_level
    }

    worker_logs {
      enabled   = var.logging_configuration.worker.enabled
      log_level = var.logging_configuration.worker.log_level
    }
  }

  tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
      component   = "mwaa"
    },
    var.tags
  )
}
