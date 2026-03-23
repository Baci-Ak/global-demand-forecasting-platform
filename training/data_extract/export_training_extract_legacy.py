"""
training.export_training_extract

Export modeling data from the warehouse into a parquet artifact.

Purpose
-------
- create a repeatable training extract outside notebooks
- establish the production pattern: warehouse -> extract artifact
- keep training separate from direct warehouse queries
"""

from __future__ import annotations

import io

import boto3
import pandas as pd
from sqlalchemy import text

from training.settings import get_training_settings
from training.data_extract.dataset import get_training_engine
from training.data_extract.config import TrainingExtractConfig




def build_training_extract_query(limit_series: int | None) -> str:
    """
    Build the SQL query for exporting a training extract.

    If limit_series is None, export the full modeling dataset.
    Otherwise, export only the top-selling item-store subset.
    """
    if limit_series is None:
        return """
        select
            id,
            item_id,
            dept_id,
            cat_id,
            store_id,
            state_id,
            d,
            date,
            wm_yr_wk,
            sales,
            sell_price,
            temperature_2m_max,
            temperature_2m_min,
            precipitation_sum,
            wind_speed_10m_max,
            cpi_all_items,
            unemployment_rate,
            federal_funds_rate,
            nonfarm_payrolls,
            trends_walmart,
            trends_grocery_store,
            trends_discount_store,
            trends_cleaning_supplies
        from gold.gold_m5_daily_feature_mart
        order by store_id, item_id, date
        """

    return f"""
    with series_rank as (
        select
            store_id,
            item_id,
            sum(sales) as total_sales
        from gold.gold_m5_daily_feature_mart
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
    join top_series t
      on g.store_id = t.store_id
     and g.item_id = t.item_id
    order by g.store_id, g.item_id, g.date
    """


def main() -> None:
    """
    Export the configured training extract to S3 in parquet chunks.
    """
    settings = get_training_settings()
    config = TrainingExtractConfig()

    query = build_training_extract_query(limit_series=config.limit_series)
    engine = get_training_engine()
    s3 = boto3.client("s3")

    total_rows = 0
    part = 0

    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]

        while True:
            rows = cursor.fetchmany(config.chunk_size)
            if not rows:
                break

            df = pd.DataFrame(rows, columns=columns)

            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            buffer.seek(0)

            key = f"{config.s3_key_prefix}/part-{part:05d}.parquet"
            s3.upload_fileobj(buffer, settings.TRAINING_EXTRACTS_BUCKET, key)

            chunk_rows = len(df)
            total_rows += chunk_rows

            print(f"Uploaded s3://{settings.TRAINING_EXTRACTS_BUCKET}/{key} ({chunk_rows:,} rows)")
            part += 1
    finally:
        conn.close()

    print("Training extract export complete.")
    print(f"Total rows: {total_rows:,}")
    print(f"Chunks written: {part}")
    print(f"S3 prefix: s3://{settings.TRAINING_EXTRACTS_BUCKET}/{config.s3_key_prefix}/")

if __name__ == "__main__":
    main()