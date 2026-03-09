"""
Weather extraction from Open-Meteo.

Purpose
-------
Fetch daily historical weather observations from the configured provider.

This module performs extraction only:
- no Bronze writes
- no audit logging
- no orchestration
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict

import requests

from app_config.config import settings


def fetch_daily_weather(
    *,
    latitude: float,
    longitude: float,
    timezone: str,
    start_date: date | None = None,
    end_date: date | None = None,
    days_back: int | None = None,
) -> Dict[str, Any]:
    """
    Fetch daily weather observations from the configured provider.

    Rules
    -----
    - If start_date and end_date are provided, use them directly.
    - Otherwise fall back to a rolling historical window using days_back.
    """

    if not settings.WEATHER_BASE_URL:
        raise RuntimeError("WEATHER_BASE_URL is not configured.")

    if start_date is not None and end_date is not None:
        fetch_start_date = start_date
        fetch_end_date = end_date
    else:
        if days_back is None:
            days_back = settings.WEATHER_DEFAULT_HISTORICAL_DAYS or 14

        fetch_end_date = date.today()
        fetch_start_date = fetch_end_date - timedelta(days=days_back)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": fetch_start_date.isoformat(),
        "end_date": fetch_end_date.isoformat(),
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": timezone,
    }
    # if the provider requires a key in the future, this supports it
    if settings.WEATHER_API_KEY:
        params["apikey"] = settings.WEATHER_API_KEY

    response = requests.get(
        settings.WEATHER_BASE_URL,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    return response.json()

