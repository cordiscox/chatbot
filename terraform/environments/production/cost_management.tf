module "cost_management" {
  source = "../../modules/cost_management"

  environment                = var.environment
  monthly_budget_amount     = 50
  budget_alert_emails       = ["tu@email.com"]  # TODO: Reemplaza con tu email real o usa una variable

  tags = {
    Environment = var.environment
    Project     = "chatbot"
    ManagedBy   = "terraform"
  }
}