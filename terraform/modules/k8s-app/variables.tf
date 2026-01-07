variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "image" {
  description = "Docker image to deploy"
  type        = string
}

variable "replicas" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API Key"
  type        = string
  sensitive   = true
}

variable "hcaptcha_secret_key" {
  description = "hCaptcha Secret Key"
  type        = string
  sensitive   = true
}

variable "model_name" {
  description = "LLM Model Name"
  type        = string
  default     = "gpt-4o-mini" 
}

variable "embedding_model_name" {
  description = "Embedding Model Name"
  type        = string
  default     = "text-embedding-3-small"
}
