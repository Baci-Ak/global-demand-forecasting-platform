"""
training.train_random_forest

Production training entrypoint for the first forecasting model candidate.

Purpose
-------
- Load modeling data from the warehouse
- Build leakage-safe forecasting features
- Create a time-based train/test split
- Train the Random Forest benchmark model
- Evaluate the model using WMAPE
- Log parameters and metrics to MLflow

Design principles
-----------------
- Keep configuration separate from execution
- Avoid hardcoding values directly inside training logic
- Keep the script reproducible and easy to operationalize later
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from training.dataset import load_top_series_subset
from training.evaluate import wmape
from training.features import FEATURE_COLUMNS, build_features, prepare_modeling_dataset
from training.mlflow_utils import configure_mlflow
from training.config import get_mlflow_tracking_uri, get_mlflow_registered_model_name



# ============================================================
# Training configuration
# ============================================================
# Purpose:
# - centralize training settings for this entrypoint
# - avoid scattering constants across the script
# - make future refactoring to env/config-driven training easier
# ============================================================


@dataclass(frozen=True)
class RandomForestTrainingConfig:
    """
    Configuration for Random Forest training.
    """

    experiment_name: str = "gdf_random_forest_demand_forecasting"
    limit_series: int = 20
    holdout_days: int = 28
    n_estimators: int = 200
    max_depth: int = 10
    random_state: int = 42
    n_jobs: int = -1


# ============================================================
# Main training workflow
# ============================================================


def main() -> None:
    """
    Train and evaluate the first production candidate on a controlled subset.
    """
    # ------------------------------------------------------------
    # Configure runtime
    # ------------------------------------------------------------
    config = RandomForestTrainingConfig()

    configure_mlflow()
    print(f"MLflow tracking URI: {get_mlflow_tracking_uri()}")
    mlflow.set_experiment(config.experiment_name)

    # ------------------------------------------------------------
    # Load dataset
    # ------------------------------------------------------------
    df = load_top_series_subset(limit_series=config.limit_series)

    # ------------------------------------------------------------
    # Build features
    # ------------------------------------------------------------
    feature_df = build_features(df)
    modeling_df = prepare_modeling_dataset(feature_df)

    # ------------------------------------------------------------
    # Time-based split: hold out the most recent N days
    # ------------------------------------------------------------
    split_date = modeling_df["date"].max() - pd.Timedelta(days=config.holdout_days - 1)

    train_df = modeling_df[modeling_df["date"] < split_date].copy()
    test_df = modeling_df[modeling_df["date"] >= split_date].copy()

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["sales"]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["sales"]

    # ------------------------------------------------------------
    # Start MLflow run
    # ------------------------------------------------------------
    with mlflow.start_run():
        # --------------------------------------------------------
        # Log run configuration
        # --------------------------------------------------------
        mlflow.log_params(asdict(config))
        mlflow.log_param("feature_count", len(FEATURE_COLUMNS))
        mlflow.log_param("feature_columns", ",".join(FEATURE_COLUMNS))

        # --------------------------------------------------------
        # Train model
        # --------------------------------------------------------
        model = RandomForestRegressor(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            random_state=config.random_state,
            n_jobs=config.n_jobs,
        )
        model.fit(X_train, y_train)

        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=get_mlflow_registered_model_name(),
        )

        # --------------------------------------------------------
        # Evaluate model
        # --------------------------------------------------------
        y_pred = model.predict(X_test)
        score = wmape(y_test, y_pred)
       

        # --------------------------------------------------------
        # Log metrics
        # --------------------------------------------------------
        mlflow.log_metric("wmape", score)
        mlflow.log_metric("train_rows", len(train_df))
        mlflow.log_metric("test_rows", len(test_df))

        # --------------------------------------------------------
        # Console summary
        # --------------------------------------------------------
        print("Random Forest training complete.")
        print(f"Experiment: {config.experiment_name}")
        print(f"Train rows: {len(train_df):,}")
        print(f"Test rows: {len(test_df):,}")
        print(f"WMAPE: {score:.4f}")


if __name__ == "__main__":
    main()