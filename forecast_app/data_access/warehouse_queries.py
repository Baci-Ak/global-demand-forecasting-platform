"""
forecast_app.data_access.warehouse_queries

Read-only warehouse query helpers for the Layer 2 forecast application.

Purpose
-------
- keep SQL and warehouse access separate from UI code
- provide reusable read-only query functions for forecast views
- keep the app focused on presentation, not connection logic

Design principles
-----------------
- read from warehouse-served production outputs only
- reuse the project's proven warehouse engine construction
- use simple, explicit SQL for the first release
- return pandas DataFrames ready for Streamlit display
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from forecast_app.settings import settings
from training.data_extract.dataset import get_training_engine


def get_redshift_engine():
    """
    Reuse the project's proven warehouse engine construction.
    """
    return get_training_engine()


def fetch_latest_forecast_freshness() -> pd.DataFrame:
    """
    Return the latest forecast freshness summary view.
    """
    query = f"""
    select *
    from {settings.FORECAST_FRESHNESS_VIEW}
    order by generated_at desc
    """

    engine = get_redshift_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def fetch_forecast_run_monitoring(limit: int = 50) -> pd.DataFrame:
    """
    Return recent forecast batch monitoring records.
    """
    query = f"""
    select *
    from {settings.FORECAST_RUN_MONITORING_VIEW}
    order by generated_at desc
    limit :limit
    """

    engine = get_redshift_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), {"limit": limit})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def fetch_forecast_rows(
    limit: int = 500,
) -> pd.DataFrame:
    """
    Return recent forecast rows for the first app release.
    """
    query = f"""
    select *
    from {settings.FORECAST_SCHEMA}.{settings.FORECAST_TABLE}
    order by generated_at desc, forecast_date asc
    limit :limit
    """

    engine = get_redshift_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), {"limit": limit})
        return pd.DataFrame(result.fetchall(), columns=result.keys())