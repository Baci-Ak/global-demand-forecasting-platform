"""
training.data_extract.unload_training_extract

Unload the production training dataset from Redshift to S3 as parquet.

Purpose
-------
- materialize a bounded production training extract outside notebook memory
- keep model training decoupled from direct warehouse scans at runtime
- let Redshift perform the heavy export work efficiently
- provide a repeatable extract contract for ECS training jobs

Design principles
-----------------
- keep SQL generation separate from execution
- bound the training horizon for production-safe retraining
- support optional top-series limiting for controlled experiments
- keep orchestration concerns out of the extract module
"""

from __future__ import annotations

from sqlalchemy import text

from training.configs.config import get_redshift_copy_role_arn
from training.data_extract.config import TrainingExtractConfig
from training.data_extract.dataset import get_training_engine
from training.settings import get_training_settings


# ============================================================
# Query builders
# ============================================================
# Purpose:
# - centralize the SQL used for production training extracts
# - keep the history window explicit and reproducible
# - support both full-series and limited-series exports
# ============================================================


def build_training_extract_query(
    limit_series: int | None,
    training_history_days: int,
) -> str:
    """
    Build the SQL query for exporting the production training extract.

    Rules
    -----
    - Anchor the training window to the latest date present in the mart,
      not to current_date.
    - Optionally restrict to a top-series subset for controlled experiments.
    """
    if limit_series is None:
        return f"""
        with max_dt as (
            select max(date) as max_date
            from gold.gold_m5_daily_feature_mart
        ),
        base as (
            select
                g.id,
                g.item_id,
                g.dept_id,
                g.cat_id,
                g.store_id,
                g.state_id,
                g.d,
                g.date,
                g.wm_yr_wk,
                g.sales,
                g.sell_price,
                g.temperature_2m_max,
                g.temperature_2m_min,
                g.precipitation_sum,
                g.wind_speed_10m_max,
                g.cpi_all_items,
                g.unemployment_rate,
                g.federal_funds_rate,
                g.nonfarm_payrolls,
                g.trends_walmart,
                g.trends_grocery_store,
                g.trends_discount_store,
                g.trends_cleaning_supplies
            from gold.gold_m5_daily_feature_mart g
            cross join max_dt m
            where g.date > dateadd(day, -{training_history_days}, m.max_date)
        )
        select *
        from base
        order by store_id, item_id, date
        """

    return f"""
    with max_dt as (
        select max(date) as max_date
        from gold.gold_m5_daily_feature_mart
    ),
    base as (
        select
            g.id,
            g.item_id,
            g.dept_id,
            g.cat_id,
            g.store_id,
            g.state_id,
            g.d,
            g.date,
            g.wm_yr_wk,
            g.sales,
            g.sell_price,
            g.temperature_2m_max,
            g.temperature_2m_min,
            g.precipitation_sum,
            g.wind_speed_10m_max,
            g.cpi_all_items,
            g.unemployment_rate,
            g.federal_funds_rate,
            g.nonfarm_payrolls,
            g.trends_walmart,
            g.trends_grocery_store,
            g.trends_discount_store,
            g.trends_cleaning_supplies
        from gold.gold_m5_daily_feature_mart g
        cross join max_dt m
        where g.date > dateadd(day, -{training_history_days}, m.max_date)
    ),
    series_rank as (
        select
            store_id,
            item_id,
            sum(sales) as total_sales
        from base
        group by store_id, item_id
    ),
    top_series as (
        select
            store_id,
            item_id
        from series_rank
        order by total_sales desc
        limit {limit_series}
    )
    select
        b.id,
        b.item_id,
        b.dept_id,
        b.cat_id,
        b.store_id,
        b.state_id,
        b.d,
        b.date,
        b.wm_yr_wk,
        b.sales,
        b.sell_price,
        b.temperature_2m_max,
        b.temperature_2m_min,
        b.precipitation_sum,
        b.wind_speed_10m_max,
        b.cpi_all_items,
        b.unemployment_rate,
        b.federal_funds_rate,
        b.nonfarm_payrolls,
        b.trends_walmart,
        b.trends_grocery_store,
        b.trends_discount_store,
        b.trends_cleaning_supplies
    from base b
    join top_series t
      on b.store_id = t.store_id
     and b.item_id = t.item_id
    order by b.store_id, b.item_id, b.date
    """


# ============================================================
# Main unload workflow
# ============================================================
# Purpose:
# - execute a Redshift UNLOAD directly to the training extracts bucket
# - avoid in-memory dataframe export in the ECS runtime
# - publish a stable parquet extract prefix for downstream training
# ============================================================


def main() -> None:
    """
    Unload the configured production training extract from Redshift to S3.
    """
    settings = get_training_settings()
    config = TrainingExtractConfig()
    engine = get_training_engine()

    if not settings.TRAINING_EXTRACTS_BUCKET:
        raise ValueError(
            "TRAINING_EXTRACTS_BUCKET is not configured. "
            "Set TRAINING_EXTRACTS_BUCKET in the environment."
        )

    query = build_training_extract_query(
        limit_series=config.limit_series,
        training_history_days=config.training_history_days,
    ).strip()

    escaped_query = query.replace("'", "''")
    s3_prefix = f"s3://{settings.TRAINING_EXTRACTS_BUCKET}/{config.s3_key_prefix}/"
    role_arn = get_redshift_copy_role_arn()

    unload_sql = f"""
    UNLOAD ('{escaped_query}')
    TO '{s3_prefix}'
    IAM_ROLE '{role_arn}'
    FORMAT AS PARQUET
    MANIFEST VERBOSE
    ALLOWOVERWRITE
    PARALLEL OFF
    """

    with engine.begin() as conn:
        conn.execute(text(unload_sql))

    print("Training extract unload complete.")
    print(f"Training history days: {config.training_history_days}")
    print(f"Series limit: {config.limit_series}")
    print(f"S3 prefix: {s3_prefix}")
    print(f"Manifest: {s3_prefix}manifest")


if __name__ == "__main__":
    main()