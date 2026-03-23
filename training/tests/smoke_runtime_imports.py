"""
training.tests.smoke_runtime_imports

Purpose
-------
Container-safe smoke test for the production ML runtime image.

Why this exists
---------------
The first ECS image validation should prove that the container can boot
and import the core ML runtime modules that are intentionally free from
external service connections.

This test must NOT require:
- MLflow server connectivity
- Postgres / Redshift connectivity
- local .env files
- SSH / SSM tunnels
- any private-network-only infrastructure

Design rules
------------
- Import only modules that should remain config-free at import time.
- Avoid importing pipeline entrypoints that currently initialize runtime
  configuration too early.
- Keep this as the canonical Docker/ECS smoke test target.
"""

from __future__ import annotations


def main() -> None:
    """
    Import core runtime modules that should be safe in a clean container.
    """
    from training.features.features import build_features, get_feature_columns, prepare_modeling_dataset
    from training.prediction.forecast_runner import get_latest_series_history, run_recursive_forecast
    from training.validation.rolling_windows import generate_rolling_splits
    from training.validation.rolling_backtest import run_rolling_backtest
    from training.evaluation.evaluate import mae, rmse, rmsse, wmape, wrmsse

    # Touch imported symbols so the smoke test is explicit and lint-friendly.
    _ = (
        build_features,
        get_feature_columns,
        prepare_modeling_dataset,
        get_latest_series_history,
        run_recursive_forecast,
        generate_rolling_splits,
        run_rolling_backtest,
        mae,
        rmse,
        rmsse,
        wmape,
        wrmsse,
    )

    print("ml runtime import smoke test passed")


if __name__ == "__main__":
    main()