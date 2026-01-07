provider "aws" {
  region = "us-east-1"
}

module "tf_state" {
  source      = "../modules/tf-state"
  bucket_name = "cordiscox-langchain-tfstate"
  table_name  = "cordiscox-langchain-tflocks"
}
