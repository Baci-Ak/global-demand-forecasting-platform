"""
Extract macroeconomic time series from the FRED API.

Purpose
-------
Fetch macroeconomic indicators from the Federal Reserve Economic Data (FRED)
API. This module performs extraction only:

- no Bronze writes
- no audit logging
- no orchestration

Those responsibilities belong to the ingestion layer.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

import requests

from app_config.config import settings


def fetch_fred_series(
    *,
    series_id: str,
    observation_start: date | None = None,
    observation_end: date | None = None,
) -> Dict[str, Any]:
    """
    Fetch a single time series from the FRED API.

    Parameters
    ----------
    series_id:
        FRED identifier for the macroeconomic series.

    observation_start:
        Optional lower bound for returned observations.

    observation_end:
        Optional upper bound for returned observations.

    Returns
    -------
    Raw JSON response from the API.
    """
    if not settings.MACRO_BASE_URL:
        raise RuntimeError("MACRO_BASE_URL is not configured.")

    if not settings.MACRO_API_KEY:
        raise RuntimeError("MACRO_API_KEY is not configured.")

    params = {
        "series_id": series_id,
        "api_key": settings.MACRO_API_KEY,
        "file_type": "json",
    }

    if observation_start is not None:
        params["observation_start"] = observation_start.isoformat()

    if observation_end is not None:
        params["observation_end"] = observation_end.isoformat()

    response = requests.get(
        settings.MACRO_BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()