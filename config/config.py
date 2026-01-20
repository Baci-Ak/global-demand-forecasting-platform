from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables (and .env for local dev).
    """

    # -------------------------
    # Postgres
    # -------------------------
    POSTGRES_DSN: str = Field(..., description="SQLAlchemy/psycopg connection string")
    AUDIT_SCHEMA: str = Field(default="audit", description="Schema for audit tables")

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_PORT: int | None = None

    # -------------------------
    # MinIO / S3
    # -------------------------
    MINIO_ROOT_USER: str | None = None
    MINIO_ROOT_PASSWORD: str | None = None
    MINIO_API_PORT: int | None = None
    MINIO_CONSOLE_PORT: int | None = None

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    MLFLOW_S3_ENDPOINT_URL: str | None = None

    # -------------------------
    # MLflow
    # -------------------------
    MLFLOW_PORT: int | None = None
    MLFLOW_TRACKING_URI: str | None = None
    MLFLOW_ARTIFACT_BUCKET: str | None = None

    # -------------------------
    # Data Lake
    # -------------------------
    BRONZE_BUCKET: str | None = None

    # -------------------------
    # Kaggle (note: treat as secret)
    # -------------------------
    KAGGLE_API_TOKEN: str | None = None
    KAGGLE_USERNAME: str | None = None
    M5_COMPETITION: str | None = None
    M5_DESTINATION: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",case_sensitive=True, extra="ignore",)


settings = Settings()
