"""
forecast_app.snapshot_export.queries

Warehouse query helpers for Layer 2 snapshot export.

Purpose
-------
- read the app-serving datasets from the warehouse
- keep export SQL separate from snapshot writing logic
- reuse the project's proven warehouse engine construction

Design principles
-----------------
- read only from warehouse-served production outputs
- keep queries explicit and easy to audit
- return pandas DataFrames ready for snapshot writing
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from forecast_app.snapshot_export.config import settings
from training.data_extract.dataset import get_training_engine


def get_warehouse_engine():
    """
    Reuse the project's proven warehouse engine construction.
    """
    return get_training_engine()


def fetch_latest_forecast_freshness() -> pd.DataFrame:
    """
    Fetch the latest forecast freshness dataset for snapshot export.
    """
    query = f"""
    select *
    from {settings.FORECAST_FRESHNESS_VIEW}
    order by generated_at desc
    """

    engine = get_warehouse_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def fetch_forecast_run_monitoring(limit: int = 500) -> pd.DataFrame:
    """
    Fetch recent forecast run monitoring records for snapshot export.
    """
    query = f"""
    select *
    from {settings.FORECAST_RUN_MONITORING_VIEW}
    order by generated_at desc
    limit :limit
    """

    engine = get_warehouse_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), {"limit": limit})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def fetch_forecast_rows(limit: int = 100000) -> pd.DataFrame:
    """
    Fetch forecast rows for snapshot export.

    Notes
    -----
    - First release keeps this simple with a bounded extract.
    - This can later be refined to export only the latest generated batch.
    """
    query = f"""
    select *
    from {settings.FORECAST_SCHEMA}.{settings.FORECAST_TABLE}
    order by generated_at desc, forecast_date asc
    limit :limit
    """

    engine = get_warehouse_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), {"limit": limit})
        return pd.DataFrame(result.fetchall(), columns=result.keys())