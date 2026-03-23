"""
training.prediction.writeback

Warehouse writeback utilities for production demand forecasts.

Purpose
-------
- persist batch forecast outputs into the warehouse
- keep forecast persistence separate from model inference logic
- create the forecast schema/table if missing
- support clean overwrite semantics for recurring batch runs

Design principles
-----------------
- keep warehouse DDL/DML out of the prediction entrypoint
- make the target schema/table explicit and reproducible
- use explicit SQLAlchemy inserts instead of pandas.to_sql
- keep the contract easy to replace later with a higher-scale COPY pattern
"""

from __future__ import annotations

from sqlalchemy import text

from training.data_extract.dataset import get_training_engine


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
# Forecast writeback
# ============================================================
# Purpose:
# - persist the prepared forecast dataframe into the warehouse
# - keep insert behavior explicit and reusable
# - provide one write path for the prediction entrypoint
# ============================================================


def write_forecast_to_warehouse(
    forecast_df,
    forecast_schema: str,
    forecast_table: str,
) -> None:
    """
    Write the forecast dataframe into the warehouse table.

    Assumptions
    -----------
    - forecast_df already contains the final warehouse contract columns.
    - overlapping forecast dates should be replaced on each batch run.
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

    insert_sql = text(
        f"""
        insert into {forecast_schema}.{forecast_table} (
            forecast_date,
            forecast_step,
            store_id,
            item_id,
            prediction,
            model_name,
            model_version,
            feature_set_name,
            generated_at
        ) values (
            :forecast_date,
            :forecast_step,
            :store_id,
            :item_id,
            :prediction,
            :model_name,
            :model_version,
            :feature_set_name,
            :generated_at
        )
        """
    )

    records = forecast_df.to_dict(orient="records")
    batch_size = 5000

    engine = get_training_engine()

    with engine.begin() as conn:
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            conn.execute(insert_sql, batch)