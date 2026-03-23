# docker/ml-runtime

Purpose:
- base container image for production ML runtime jobs on ECS

Initial jobs:
- training.data.export_training_extract
- training.pipelines.train_lightgbm
- training.pipelines.predict_next_28_days

Notes:
- image will be pushed to the Terraform-managed ECR repository
- ECS tasks will use this image
- MWAA will later trigger these ECS tasks