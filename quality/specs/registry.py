"""
quality.specs.registry

Central registry of dataset DQ specifications.

This allows orchestration code to reference datasets by name and discover
their expectations/suites without importing individual spec modules everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class DqSpec:
    dataset_name: str
    suite_name: str
    bronze_filename: str


# -------------------------
# Registered specs
# -------------------------
M5_CALENDAR: Final[DqSpec] = DqSpec(
    dataset_name="m5_calendar",
    suite_name="calendar_basic_v1",
    bronze_filename="calendar.csv",
)

M5_SELL_PRICES: Final[DqSpec] = DqSpec(
    dataset_name="m5_sell_prices",
    suite_name="sell_prices_basic_v1",
    bronze_filename="sell_prices.csv",
)

ALL_SPECS: Final[tuple[DqSpec, ...]] = (M5_CALENDAR, M5_SELL_PRICES)
