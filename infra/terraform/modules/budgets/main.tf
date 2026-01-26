/*
  Module: budgets
  File: main.tf

  Creates:
  - A monthly COST budget with alert thresholds

  Implementation details:
  - Uses aws_budgets_budget (Cost budget)
  - Alerts at 80% actual spend and 100% forecasted spend by default
*/

resource "aws_budgets_budget" "monthly_cost" {
  name         = var.budget_name
  budget_type  = "COST"
  time_unit    = "MONTHLY"
  limit_amount = tostring(var.limit_usd)
  limit_unit   = "USD"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.alert_emails
  }
}
