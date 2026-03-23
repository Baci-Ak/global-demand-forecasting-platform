module "ml_ecr" {
  source = "../../../modules/ecr"

  repository_name = "gdf-prod-ml-runtime"

  tags = {
    project     = "gdf"
    environment = "prod"
  }
}