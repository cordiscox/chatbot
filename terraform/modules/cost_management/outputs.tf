output "budget_arn" {
  description = "ARN of the AWS Budget"
  value       = aws_budgets_budget.monthly.arn
}

output "anomaly_monitor_arn" {
  description = "ARN of the Cost Anomaly Monitor"
  value       = aws_ce_anomaly_monitor.main.arn
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  value       = aws_s3_bucket.logs.id
}
