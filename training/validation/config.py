from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RollingBacktestConfig:
    """
    Shared configuration for rolling-window time-series validation.
    """

    horizon_days: int = 28
    n_windows: int = 5
    date_column: str = "date"
    target_column: str = "sales"