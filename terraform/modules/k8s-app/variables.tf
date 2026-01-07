variable "app_name" {
  type = string
}

variable "image" {
  type = string
}

variable "replicas" {
  type    = number
  default = 1
}

variable "database_url" {
  type = string
  # Default to a dummy value if no DB is ready yet
  default = "postgresql://user:pass@localhost:5432/db" 
}