"""
Dashboard runtime configuration.

Purpose
-------
Central location for environment-driven configuration so the dashboard
never hardcodes infrastructure details.

The dashboard supports multiple data backends:
- warehouse: direct connection to analytics warehouse
- extract: portable local/remote extract files for decoupled deployment
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dashboard.core.constants import (
    APP_ICON,
    APP_NAME,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_DATE_WINDOW_DAYS,
    DEFAULT_LAYOUT,
)


def _env(key: str, default: str | None = None) -> str | None:
    """Read an environment variable safely."""
    return os.getenv(key, default)


@dataclass(frozen=True)
class DashboardConfig:
    """
    Immutable runtime configuration for the dashboard.
    """

    # App identity
    app_name: str = APP_NAME
    app_icon: str = APP_ICON
    layout: str = DEFAULT_LAYOUT

    # Data backend selection
    data_backend: str = (_env("DASHBOARD_DATA_BACKEND", "extract") or "extract").lower()

    # Warehouse connection
    warehouse_dsn: str | None = _env("WAREHOUSE_DSN")

    # Extract-backed deployment
    extract_base_path: str = _env("DASHBOARD_EXTRACT_BASE_PATH", "dashboard/data") or "dashboard/data"
    extract_format: str = (_env("DASHBOARD_EXTRACT_FORMAT", "parquet") or "parquet").lower()

    # Dashboard behavior
    default_date_window_days: int = DEFAULT_DATE_WINDOW_DAYS
    cache_ttl_seconds: int = int(
        _env("DASHBOARD_CACHE_TTL_SECONDS", str(DEFAULT_CACHE_TTL_SECONDS))
        or DEFAULT_CACHE_TTL_SECONDS
    )

    # Feature flags
    enable_export: bool = (
        _env("DASHBOARD_ENABLE_EXPORT", "true").lower() == "true"
    )
    enable_debug_panels: bool = (
        _env("DASHBOARD_ENABLE_DEBUG_PANELS", "false").lower() == "true"
    )


CONFIG = DashboardConfig()