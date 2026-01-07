output "vpc_id" {
  value = module.networking.vpc_id
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

# output "load_balancer_hostname" {
#   value = module.k8s_app.load_balancer_hostname
# }

output "github_actions_role_arn" {
  value = module.github_oidc.role_arn
  description = "The ARN of the IAM role for GitHub Actions to use in secrets"
}
