# AWS Budget
resource "aws_budgets_budget" "monthly" {
  name              = "${var.environment}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = var.monthly_budget_amount
  limit_unit        = "USD"
  time_period_start = "2025-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 50
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  cost_types {
    include_credit             = false
    include_discount          = false
    include_other_subscription = true
    include_recurring         = true
    include_refund           = false
    include_subscription     = true
    include_support          = true
    include_tax             = true
    include_upfront         = true
    use_amortized          = false
    use_blended            = false
  }

  # Filter by tag to only track costs for this environment/project
  # Note: Requires "Environment" tag to be active in Cost Allocation Tags
  cost_filter {
    name = "TagKeyValue"
    values = ["user:Environment$${var.environment}"]
  }

  tags = var.tags
}

# Cost Anomaly Detection
resource "aws_ce_anomaly_monitor" "main" {
  name              = "${var.environment}-cost-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "main" {
  name              = "${var.environment}-anomaly-subscription"
  frequency         = "DAILY"
  monitor_arn_list  = [aws_ce_anomaly_monitor.main.arn]
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
      values        = ["10.0"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  subscriber {
    type    = "EMAIL"
    address = var.budget_alert_emails[0]
  }
}

# S3 Lifecycle Rules for Cost Optimization (Generic Logs)
resource "aws_s3_bucket" "logs" {
  bucket = "${var.environment}-logs-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-logs"
    }
  )
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "log_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 60
      storage_class = "GLACIER"
    }

    expiration {
      days = 90
    }
  }
}

data "aws_caller_identity" "current" {}