"""
Extract search-interest time series from Google Trends.

Purpose
-------
Fetch search-intent data using pytrends.

This module performs extraction only:
- no Bronze writes
- no audit logging
- no orchestration
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from pytrends.request import TrendReq

from app_config.config import settings


def make_trend_client() -> TrendReq:
    """
    Create one reusable pytrends client.

    Notes
    -----
    - Reuse the same client across many chunk requests to reduce repeated token
      setup and session churn.
    - pytrends supports retries/backoff_factor/proxies in TrendReq.
    """
    return TrendReq(
        hl="en-US",
        tz=0,
        retries=3,
        backoff_factor=0.5,
        proxies=getattr(settings, "TRENDS_PROXIES", None) or [],
        requests_args={"timeout": (10, 30)},
    )


def fetch_interest_over_time(
    *,
    pytrends: TrendReq,
    keyword: str,
    start_date: date,
    end_date: date,
    geo: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch Google Trends interest-over-time data for a single keyword and window.

    Parameters
    ----------
    pytrends:
        Reusable TrendReq client.

    keyword:
        Search term to query.

    start_date:
        Inclusive lower bound for the timeframe.

    end_date:
        Inclusive upper bound for the timeframe.

    geo:
        Optional geographic code (defaults to settings.TRENDS_GEO or "US").

    Returns
    -------
    pandas.DataFrame
        Trends time series with one row per date.
    """
    resolved_geo = geo or settings.TRENDS_GEO or "US"
    timeframe = f"{start_date.isoformat()} {end_date.isoformat()}"

    pytrends.build_payload(
        kw_list=[keyword],
        cat=0,
        timeframe=timeframe,
        geo=resolved_geo,
        gprop="",
    )

    df = pytrends.interest_over_time()

    if df.empty:
        raise RuntimeError(f"No Google Trends data returned for keyword={keyword}")

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    return df.reset_index()