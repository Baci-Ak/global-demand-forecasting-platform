"""
training.dataset

Dataset loading utilities for model training.

Purpose
-------
- Load modeling data from the warehouse
- Keep SQL access separate from feature engineering and training logic
- Reuse the project's configured warehouse connection pattern
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text

from training.config import get_warehouse_dsn


def get_training_engine():
    """
    Create and return a SQLAlchemy engine for training data access.
    """
    return create_engine(get_warehouse_dsn())


def load_top_series_subset(limit_series: int = 20) -> pd.DataFrame:
    """
    Load a controlled subset of the top-selling item-store series.

    Parameters
    ----------
    limit_series : int, default=20
        Number of top item-store series to load, ranked by total sales.

    Returns
    -------
    pd.DataFrame
        Subset of `gold.gold_m5_daily_feature_mart`, ordered by
        store_id, item_id, and date.
    """
    query = f"""
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

    engine = get_training_engine()

    with engine.begin() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    return df




def load_full_modeling_dataset() -> pd.DataFrame:
    """
    Load the full modeling dataset from the Gold feature mart.

    Returns
    -------
    pd.DataFrame
        Full contents of `gold.gold_m5_daily_feature_mart`,
        ordered by store_id, item_id, and date.
    """
    query = """
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

    engine = get_training_engine()

    with engine.begin() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    return df