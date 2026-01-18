import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class S3Config:
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    bronze_bucket: str


def load_s3_config() -> S3Config:
    endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL")  # reuse for MinIO endpoint
    access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    bronze_bucket = os.getenv("BRONZE_BUCKET", "")

    if not endpoint_url:
        raise RuntimeError("MLFLOW_S3_ENDPOINT_URL is not set in .env (used as MinIO endpoint).")
    if not access_key_id or not secret_access_key:
        raise RuntimeError("AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set in .env.")
    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET not set in .env.")

    return S3Config(
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bronze_bucket=bronze_bucket,
    )


def get_s3_client(cfg: Optional[S3Config] = None):
    cfg = cfg or load_s3_config()

    # These settings help with local S3-compatible storage (MinIO)
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    return s3


def upload_file_to_bronze(local_path: Path, s3_key: str, cfg: Optional[S3Config] = None) -> str:
    """
    Upload a local file to the Bronze bucket under the given key.
    Returns the s3:// path.
    """
    cfg = cfg or load_s3_config()
    s3 = get_s3_client(cfg)

    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(str(local_path))

    s3.upload_file(str(local_path), cfg.bronze_bucket, s3_key)
    return f"s3://{cfg.bronze_bucket}/{s3_key}"
