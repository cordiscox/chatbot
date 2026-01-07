variable "environment" {
  description = "The environment name"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "eks_security_group_id" {
  description = "The security group ID of the EKS cluster nodes"
  type        = string
}
