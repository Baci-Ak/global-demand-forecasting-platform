"""
training.prediction.predict_next_28_days

Batch prediction entrypoint for generating the next 28 days of demand forecasts.

Purpose
-------
- load the latest registered production model from MLflow
- load production historical data from the training extract contract
- generate recursive 28-day forecasts
- write forecast outputs into the warehouse
- optionally persist a local debug artifact

Design principles
-----------------
- keep model loading separate from forecast generation
- reuse the same bounded extract contract used by training
- treat the warehouse as the system of record for forecast outputs
- keep local file output optional rather than the primary serving path
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from training.configs.config import get_lightgbm_registered_model_name
from training.data_extract.dataset import load_modeling_dataset_from_s3
from training.features.features import build_features
from training.prediction.forecast_runner import (
    get_latest_series_history,
    run_recursive_forecast,
)
from training.prediction.inference import load_latest_model
from training.prediction.writeback import write_forecast_to_warehouse
from .config import PredictionConfig


# ============================================================
# Forecast dataframe enrichment
# ============================================================
# Purpose:
# - attach model metadata to forecast outputs
# - prepare the warehouse write contract in one place
# - keep the prediction entrypoint clean and explicit
# ============================================================


def prepare_forecast_writeback_df(
    forecast_df,
    *,
    feature_set_name: str,
    model_version: str,
):
    """
    Prepare the final forecast dataframe for warehouse persistence.
    """
    enriched_df = forecast_df.copy()

    enriched_df["forecast_date"] = enriched_df["forecast_date"].dt.date
    enriched_df["model_name"] = get_lightgbm_registered_model_name()
    enriched_df["model_version"] = model_version
    enriched_df["feature_set_name"] = feature_set_name
    enriched_df["generated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

    return enriched_df[
        [
            "forecast_date",
            "forecast_step",
            "store_id",
            "item_id",
            "prediction",
            "model_name",
            "model_version",
            "feature_set_name",
            "generated_at",
        ]
    ]


# ============================================================
# Main prediction workflow
# ============================================================
# Purpose:
# - load the current production model
# - load bounded historical data for inference
# - generate the next 28 days of recursive forecasts
# - write forecasts into the warehouse
# - optionally write a local debug artifact
# ============================================================


def main() -> None:
    """
    Generate the next 28 days of forecasts for the production scope.
    """
    # ------------------------------------------------------------
    # Configure runtime
    # ------------------------------------------------------------
    config = PredictionConfig()

    # ------------------------------------------------------------
    # Load registered production model
    # ------------------------------------------------------------
    model, model_version = load_latest_model()

    # ------------------------------------------------------------
    # Load historical data from the production extract contract
    # ------------------------------------------------------------
    df = load_modeling_dataset_from_s3("ml/training_extracts/full")
    feature_df = build_features(df)

    # ------------------------------------------------------------
    # Keep only recent history needed for recursive forecasting
    # ------------------------------------------------------------
    history_df = get_latest_series_history(
        feature_df,
        history_days=config.history_days,
    )

    # ------------------------------------------------------------
    # Generate forecasts
    # ------------------------------------------------------------
    forecast_df = run_recursive_forecast(
        model=model,
        history_df=history_df,
        forecast_horizon=config.forecast_horizon,
        feature_set_name=config.feature_set_name,
    )

    # ------------------------------------------------------------
    # Prepare warehouse writeback dataframe
    # ------------------------------------------------------------
    forecast_write_df = prepare_forecast_writeback_df(
        forecast_df,
        feature_set_name=config.feature_set_name,
        model_version=model_version,
    )

    # ------------------------------------------------------------
    # Write forecasts to warehouse
    # ------------------------------------------------------------
    # write_forecast_to_warehouse(
    #     forecast_df=forecast_write_df,
    #     forecast_schema=config.forecast_schema,
    #     forecast_table=config.forecast_table,
    # )

    write_forecast_to_warehouse(
        forecast_df=forecast_write_df,
        forecast_schema=config.forecast_schema,
        forecast_table=config.forecast_table,
        staging_s3_prefix=config.forecast_staging_s3_prefix,
        write_chunksize=config.forecast_write_chunksize,
        )

    # ------------------------------------------------------------
    # Optional local debug artifact
    # ------------------------------------------------------------
    if config.write_local_artifact:
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / config.output_filename
        forecast_write_df.to_parquet(output_path, index=False)

        print(f"Local forecast artifact written to: {output_path}")

    # ------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------
    print("Batch forecast generation complete.")
    print(f"Forecast rows: {len(forecast_write_df):,}")
    print(
        "Forecast date range: "
        f"{forecast_write_df['forecast_date'].min()} -> "
        f"{forecast_write_df['forecast_date'].max()}"
    )
    print(f"Model version: {model_version}")
    print(f"Forecast target table: {config.forecast_schema}.{config.forecast_table}")
    print()
    print(forecast_write_df.head(20))


if __name__ == "__main__":
    main()