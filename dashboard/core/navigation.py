"""
Dashboard navigation registry.

Purpose
-------
Defines the sidebar navigation in one place so page routing is centralized
and scalable as the dashboard grows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageDefinition:
    """Single dashboard page registration."""

    key: str
    label: str
    module_path: str


PAGE_REGISTRY: tuple[PageDefinition, ...] = (
    PageDefinition(
        key="executive_overview",
        label="Executive Overview",
        module_path="dashboard.views.executive_overview",
    ),
    PageDefinition(
        key="sales_demand",
        label="Sales & Demand",
        module_path="dashboard.views.sales_demand",
    ),
    PageDefinition(
        key="pricing_commercial",
        label="Pricing & Commercial",
        module_path="dashboard.views.pricing_commercial",
    ),
    PageDefinition(
        key="external_drivers",
        label="External Drivers",
        module_path="dashboard.views.external_drivers",
    ),
    PageDefinition(
        key="store_item_drilldown",
        label="Store / Item Drilldown",
        module_path="dashboard.views.store_item_drilldown",
    ),
    PageDefinition(
        key="forecast_readiness",
        label="Forecast Readiness",
        module_path="dashboard.views.forecast_readiness",
    ),
    PageDefinition(
        key="data_quality_freshness",
        label="Data Quality & Freshness",
        module_path="dashboard.views.data_quality_freshness",
    ),
)