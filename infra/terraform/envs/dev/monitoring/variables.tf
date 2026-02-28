variable "project_name" {
  type    = string
  default = "gdf"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# Where alerts go (email). You can later add Slack via Chatbot, PagerDuty, etc.
variable "alert_emails" {
  type        = list(string)
  description = "List of email addresses to subscribe to SNS alerts."
}

# Monthly cost budget in USD.
variable "monthly_budget_usd" {
  type        = number
  description = "Monthly AWS cost budget amount (USD)."
}

# Percent thresholds that trigger alerts.
variable "budget_alert_thresholds_percent" {
  type        = list(number)
  default     = [80, 100]
  description = "Budget alert thresholds in percent (e.g., 80, 100)."
}


# -----------------------------
# Alarm evaluation defaults
# -----------------------------
variable "alarm_period_seconds" {
  description = "CloudWatch alarm period in seconds (e.g., 60, 300)."
  type        = number
  default     = 300
}

variable "alarm_evaluation_periods" {
  description = "How many periods to evaluate before alarm triggers."
  type        = number
  default     = 3
}

variable "alarm_datapoints_to_alarm" {
  description = "How many datapoints must be breaching within evaluation_periods."
  type        = number
  default     = 2
}


# -----------------------------------------------------------
#Turn on RDS Postgres Production-Grade Alerts (CloudWatch → SNS)
# -------------------------------------------------------------

#variable "rds_instance_id" {
#description = "RDS instance identifier (DBInstanceIdentifier) to alarm on."
#type        = string
#}

variable "rds_cpu_high_threshold" {
  description = "CPU utilization % threshold for alarm."
  type        = number
  default     = 80
}

variable "rds_free_storage_low_threshold_bytes" {
  description = "Free storage bytes threshold for alarm (e.g., 10GB = 10737418240)."
  type        = number
  default     = 10737418240
}

variable "rds_connections_high_threshold" {
  description = "DatabaseConnections threshold for alarm."
  type        = number
  default     = 200
}





# ------------------------------------------------------------------------------
# Redshift Serverless alarm thresholds
# ------------------------------------------------------------------------------

variable "redshift_rrpu_utilization_high_threshold" {
  description = "Alarm threshold for Redshift Serverless RPUUtilization (percent)."
  type        = number
  default     = 80
}

variable "redshift_connections_high_threshold" {
  description = "Alarm threshold for Redshift Serverless DatabaseConnections."
  type        = number
  default     = 200
}


variable "rds_freeable_memory_low_threshold_bytes" {
  description = "Alarm threshold for RDS FreeableMemory (bytes)."
  type        = number
  default     = 268435456 # 256 MiB
}

variable "rds_disk_queue_depth_high_threshold" {
  description = "Alarm threshold for RDS DiskQueueDepth."
  type        = number
  default     = 64
}