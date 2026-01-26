/*
  File: outputs.tf
*/

output "budget_name" {
  description = "Created budget name."
  value       = aws_budgets_budget.monthly_cost.name
}
