import mlflow
from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()


# Point MLflow client to the running MLflow server
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001"))


# Use (or create) an experiment
mlflow.set_experiment("local_smoke_test")

os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "")


with mlflow.start_run(run_name="hello_mlflow"):
    # Log a simple parameter and metric
    mlflow.log_param("example_param", 1)
    mlflow.log_metric("example_metric", 0.123)

    # Create a tiny artifact file
    artifact_path = Path("hello.txt")
    artifact_path.write_text("MLflow is working end-to-end.")

    # Log artifact to MinIO (S3)
    mlflow.log_artifact(str(artifact_path))

print("MLflow test run completed successfully.")
