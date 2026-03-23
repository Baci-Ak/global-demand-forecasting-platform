module "ml_ecr" {
  source = "../../../modules/ecr"

  repository_name = "gdf-ml-runtime"

  tags = {
    project     = "gdf"
    environment = "dev"
  }
}