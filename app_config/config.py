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
    AWS_REGION: str = Field(default="us-east-1", description="AWS/S3 region for boto3 clients")


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

    # -------------------------
    # Ingestion sources
    # -------------------------
    # m5 kaggle
    M5_SOURCE_NAME: str | None = None

    #whether external source (API)
    WEATHER_SOURCE_NAME: str | None = None
    WEATHER_PROVIDER: str | None = None
    WEATHER_BASE_URL: str | None = None
    WEATHER_API_KEY: str | None = None
    WEATHER_DEFAULT_HISTORICAL_DAYS: int | None = None



    # -------------------------
    # Macro (FRED)
    # -------------------------
    MACRO_SOURCE_NAME: str | None = None
    MACRO_PROVIDER: str | None = None
    MACRO_BASE_URL: str | None = None
    MACRO_API_KEY: str | None = None



    TRENDS_SOURCE_NAME: str | None = None
    TRENDS_PROVIDER: str | None = None
    TRENDS_GEO: str | None = None


    # -------------------------
    # Warehouse / Staging
    # -------------------------
    STAGING_SCHEMA: str = Field(default="staging", description="Schema for warehouse tables")
    #STAGING_TABLE: str = Field(default="m5_calendar_raw", description="m5_calendar staging raw table for warehouse")
    #STAGING_TABLE_sell_prices: str = Field(default="m5_sell_prices_raw", description="m5_sell_prices_raw staging raw table for warehouse")

    # -------------------------
    # Warehouse / Silver
    # -------------------------
    SILVER_SCHEMA: str = Field(default="silver", description="Schema for cleaned / typed silver tables")

    WAREHOUSE_DSN: str | None = Field(
    default=None,
    description="SQLAlchemy connection string for the warehouse (Postgres local or Redshift in AWS). If not set, defaults to POSTGRES_DSN.",
)
    # aws redshift i am role ARN
    REDSHIFT_IAM_ROLE_ARN: str | None = Field(
    default=None,
    description="IAM Role ARN used by Redshift COPY/UNLOAD to access S3",
)



    


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",case_sensitive=True, extra="ignore",)


settings = Settings()
