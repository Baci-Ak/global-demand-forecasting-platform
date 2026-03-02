terraform {
  backend "s3" {
    bucket         = "gdf-dev-tfstate-f6df28"
    key            = "envs/dev/monitoring/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "gdf-dev-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
      component   = "monitoring"
    }
  }
}