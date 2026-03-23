from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TrainingSettings(BaseSettings):
    """
    Settings required by ML training / inference runtime only.

    Design goals
    ------------
    - Do not require unrelated app settings such as audit Postgres config.
    - Keep ECS / local / future batch jobs lightweight and explicit.
    - Allow warehouse + MLflow configuration to evolve independently.
    """

    AWS_REGION: str = Field(default="us-east-1")

    MLFLOW_TRACKING_URI: str | None = None
    WAREHOUSE_DSN: str | None = None

    MLFLOW_ARTIFACT_BUCKET: str | None = None
    MLFLOW_S3_ENDPOINT_URL: str | None = None

    TRAINING_EXTRACTS_BUCKET: str | None = None


    REDSHIFT_COPY_ROLE_ARN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_training_settings() -> TrainingSettings:
    return TrainingSettings()