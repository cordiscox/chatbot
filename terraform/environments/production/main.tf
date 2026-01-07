terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "networking" {
  source             = "../../modules/networking"
  environment        = var.environment
  vpc_cidr           = "10.0.0.0/16"
  public_subnets     = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets    = ["10.0.3.0/24", "10.0.4.0/24"]
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
  cluster_name       = "${var.environment}-cluster"
}

module "ecr" {
  source          = "../../modules/ecr"
  environment     = var.environment
}

module "eks" {
  source            = "../../modules/eks"
  cluster_name      = "${var.environment}-cluster"
  subnet_ids        = module.networking.private_subnet_ids
  node_desired_size = 2
  node_max_size     = 3
  node_min_size     = 1
}

/*
# Configure Kubernetes provider to use the EKS cluster
data "aws_eks_cluster" "cluster" {
  name = module.eks.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

module "k8s_app" {
  source       = "../../modules/k8s-app"
  app_name     = "chatbot"
  image        = "${module.ecr.repository_url}:${var.image_tag}"
  replicas     = 2
  database_url = "postgresql://user:pass@db-host:5432/db" # Update with real RDS endpoint later
  
  depends_on = [module.eks]
}
*/

module "github_oidc" {
  source      = "../../modules/github_oidc"
  github_org  = "cordiscox"
  github_repo = "langchain"
}
