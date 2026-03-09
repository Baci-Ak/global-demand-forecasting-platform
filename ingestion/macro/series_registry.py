"""
Macro series registry for the FRED source.

Purpose
-------
Keep the list of macroeconomic series separate from extraction logic so the
platform can scale cleanly as we add or change indicators.

Design
------
- One registry entry per upstream series.
- `series_id` is the provider's identifier.
- `feature_name` is the stable internal name we will use downstream.
"""

from __future__ import annotations


MACRO_SERIES = [
    {
        "series_id": "CPIAUCSL",
        "feature_name": "cpi_all_items",
        "label": "Consumer Price Index for All Urban Consumers: All Items",
        "frequency": "monthly",
        "units": "index",
    },
    {
        "series_id": "UNRATE",
        "feature_name": "unemployment_rate",
        "label": "Unemployment Rate",
        "frequency": "monthly",
        "units": "percent",
    },
    {
        "series_id": "FEDFUNDS",
        "feature_name": "federal_funds_rate",
        "label": "Effective Federal Funds Rate",
        "frequency": "monthly",
        "units": "percent",
    },
    {
        "series_id": "PAYEMS",
        "feature_name": "nonfarm_payrolls",
        "label": "All Employees, Total Nonfarm",
        "frequency": "monthly",
        "units": "thousands",
    },
]