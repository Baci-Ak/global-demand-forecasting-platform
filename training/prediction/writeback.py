"""
training.prediction.writeback

Warehouse writeback utilities for production demand forecasts.

Purpose
-------
- persist batch forecast outputs into the warehouse
- keep forecast persistence separate from model inference logic
- create the forecast schema/table if missing
- support clean overwrite semantics for recurring batch runs
- use Redshift COPY for production-grade forecast loading

Design principles
-----------------
- keep warehouse DDL/DML out of the prediction entrypoint
- make the target schema/table explicit and reproducible
- stage forecast files in S3 before warehouse loading
- use Redshift COPY rather than row-by-row inserts for production performance
- keep the write contract simple, observable, and replaceable later if needed
"""

from __future__ import annotations

import io
from uuid import uuid4

import boto3
import pandas as pd
from sqlalchemy import text

from training.configs.config import get_redshift_copy_role_arn
from training.data_extract.dataset import get_training_engine
from training.settings import get_training_settings


# ============================================================
# Warehouse forecast contract
# ============================================================
# Purpose:
# - define the target table shape for forecast persistence
# - keep the warehouse contract explicit in one place
# - support predictable downstream consumption
# ============================================================


def ensure_forecast_table(
    forecast_schema: str,
    forecast_table: str,
) -> None:
    """
    Ensure the forecast schema and table exist.

    Notes
    -----
    - The table is created in the warehouse database.
    - The schema is a namespace inside that database, not a separate database.
    """
    engine = get_training_engine()

    create_schema_sql = f"""
    create schema if not exists {forecast_schema}
    """

    create_table_sql = f"""
    create table if not exists {forecast_schema}.{forecast_table} (
        forecast_date date encode zstd,
        forecast_step integer encode zstd,
        store_id varchar(32) encode zstd,
        item_id varchar(64) encode zstd,
        prediction double precision encode zstd,
        model_name varchar(255) encode zstd,
        model_version varchar(64) encode zstd,
        feature_set_name varchar(255) encode zstd,
        generated_at timestamp encode zstd
    )
    diststyle auto
    sortkey (forecast_date, store_id, item_id)
    """

    with engine.begin() as conn:
        conn.execute(text(create_schema_sql))
        conn.execute(text(create_table_sql))


# ============================================================
# Idempotent overwrite helpers
# ============================================================
# Purpose:
# - keep repeated batch runs safe
# - remove overlapping forecast horizons before insert
# - avoid duplicate forecasts for the same dates
# ============================================================


def delete_existing_forecast_horizon(
    forecast_schema: str,
    forecast_table: str,
    min_forecast_date,
    max_forecast_date,
) -> None:
    """
    Delete existing rows for the incoming forecast horizon.
    """
    engine = get_training_engine()

    delete_sql = f"""
    delete from {forecast_schema}.{forecast_table}
    where forecast_date between :min_forecast_date and :max_forecast_date
    """

    with engine.begin() as conn:
        conn.execute(
            text(delete_sql),
            {
                "min_forecast_date": min_forecast_date,
                "max_forecast_date": max_forecast_date,
            },
        )


# ============================================================
# S3 staging helpers
# ============================================================
# Purpose:
# - write forecast batches to S3 as parquet
# - provide a stable Redshift COPY source path
# - isolate S3 staging behavior from warehouse SQL logic
# ============================================================


def stage_forecast_batch_to_s3(
    forecast_df: pd.DataFrame,
    staging_s3_prefix: str,
) -> tuple[str, str]:
    """
    Stage the forecast dataframe to S3 as a parquet file.

    Returns
    -------
    tuple[str, str]
        S3 bucket name and object key for the staged parquet file.
    """
    settings = get_training_settings()

    if not settings.TRAINING_EXTRACTS_BUCKET:
        raise ValueError(
            "TRAINING_EXTRACTS_BUCKET is not configured. "
            "Set TRAINING_EXTRACTS_BUCKET in the environment."
        )

    bucket = settings.TRAINING_EXTRACTS_BUCKET
    object_key = (
        f"{staging_s3_prefix.rstrip('/')}/"
        f"run_{uuid4().hex}/"
        "forecast_batch.parquet"
    )

    buffer = io.BytesIO()
    forecast_df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=buffer.getvalue(),
    )

    return bucket, object_key


# ============================================================
# Redshift COPY helpers
# ============================================================
# Purpose:
# - load staged parquet forecast files into Redshift efficiently
# - keep COPY SQL generation separate from orchestration logic
# - reuse the configured Redshift COPY role
# ============================================================


def copy_staged_forecast_to_warehouse(
    *,
    bucket: str,
    object_key: str,
    forecast_schema: str,
    forecast_table: str,
) -> None:
    """
    COPY one staged parquet forecast batch from S3 into Redshift.
    """
    engine = get_training_engine()
    role_arn = get_redshift_copy_role_arn()
    s3_uri = f"s3://{bucket}/{object_key}"

    copy_sql = f"""
    copy {forecast_schema}.{forecast_table} (
        forecast_date,
        forecast_step,
        store_id,
        item_id,
        prediction,
        model_name,
        model_version,
        feature_set_name,
        generated_at
    )
    from '{s3_uri}'
    iam_role '{role_arn}'
    format as parquet
    """

    with engine.begin() as conn:
        conn.execute(text(copy_sql))


# ============================================================
# Forecast writeback
# ============================================================
# Purpose:
# - persist the prepared forecast dataframe into the warehouse
# - use S3 staging + Redshift COPY for production-grade performance
# - provide one write path for the prediction entrypoint
# ============================================================


def write_forecast_to_warehouse(
    forecast_df,
    forecast_schema: str,
    forecast_table: str,
    staging_s3_prefix: str,
    write_chunksize: int,
) -> None:
    """
    Write the forecast dataframe into the warehouse table.

    Assumptions
    -----------
    - forecast_df already contains the final warehouse contract columns.
    - overlapping forecast dates should be replaced on each batch run.
    - forecast batches are staged to S3 and loaded with Redshift COPY.
    """
    if forecast_df.empty:
        raise ValueError("forecast_df is empty. Nothing to write to the warehouse.")

    ensure_forecast_table(
        forecast_schema=forecast_schema,
        forecast_table=forecast_table,
    )

    delete_existing_forecast_horizon(
        forecast_schema=forecast_schema,
        forecast_table=forecast_table,
        min_forecast_date=forecast_df["forecast_date"].min(),
        max_forecast_date=forecast_df["forecast_date"].max(),
    )

    total_rows = len(forecast_df)

    for start in range(0, total_rows, write_chunksize):
        batch_df = forecast_df.iloc[start:start + write_chunksize].copy()

        bucket, object_key = stage_forecast_batch_to_s3(
            forecast_df=batch_df,
            staging_s3_prefix=staging_s3_prefix,
        )

        copy_staged_forecast_to_warehouse(
            bucket=bucket,
            object_key=object_key,
            forecast_schema=forecast_schema,
            forecast_table=forecast_table,
        )