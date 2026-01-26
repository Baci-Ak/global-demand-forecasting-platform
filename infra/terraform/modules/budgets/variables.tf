/*
  Module: budgets

  Purpose:
  - Create AWS Budgets to prevent surprise spend.
  - This is a foundational production guardrail before CI/CD and orchestration.

  Notes:
  - Budgets require an email address for alerts.
  - Keep thresholds conservative in dev.
*/

variable "budget_name" {
  description = "Human-readable name for the budget."
  type        = string
}

variable "limit_usd" {
  description = "Monthly cost limit in USD."
  type        = number
}

variable "alert_emails" {
  description = "List of email addresses that will receive budget alerts."
  type        = list(string)
}
