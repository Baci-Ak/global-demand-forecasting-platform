"""
training.train_lightgbm

Production training entrypoint for the LightGBM forecasting model.

Purpose
-------
- Train a boosted-tree forecasting model
- Run rolling backtesting
- Compare performance against the Random Forest benchmark
- Log experiments, metrics, and feature importance to MLflow

Design principles
-----------------
- Keep configuration separate from execution
- Avoid hardcoding values directly inside training logic
- Keep the script reproducible and easy to operationalize later
"""

from __future__ import annotations

from dataclasses import asdict


import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import pandas as pd

from training.validation.rolling_backtest import run_rolling_backtest
from training.configs.config import (
    get_lightgbm_registered_model_name,
    get_mlflow_tracking_uri,
)
from training.data_extract.dataset import load_modeling_dataset_from_s3, load_top_series_subset
from training.features.features import (
    build_features,
    get_feature_columns,
    prepare_modeling_dataset,
)
from training.utils.mlflow_utils import configure_mlflow

from training.validation.config import RollingBacktestConfig

from .config import LightGBMTrainingConfig


# ============================================================
# Model builder
# ============================================================
# Purpose:
# - create a fresh model instance for each backtest window
# - keep model construction separate from training workflow logic
# ============================================================


def build_model(config: LightGBMTrainingConfig) -> lgb.LGBMRegressor:
    """
    Build a LightGBM model instance.
    """
    return lgb.LGBMRegressor(
        objective="regression",
        num_leaves=config.num_leaves,
        learning_rate=config.learning_rate,
        n_estimators=config.n_estimators,
        random_state=config.random_state,
        n_jobs=-1,
    )


# ============================================================
# Explainability helpers
# ============================================================
# Purpose:
# - make model behavior easier to inspect before production use
# - log feature importance artifacts to MLflow
# - support debugging and future feature-engineering decisions
# ============================================================


def log_feature_importance(
    model: lgb.LGBMRegressor,
    feature_columns: list[str],
) -> None:
    """
    Log LightGBM feature importance to MLflow.

    Parameters
    ----------
    model : lgb.LGBMRegressor
        Fitted LightGBM model.
    feature_columns : list[str]
        Feature columns used during model training.
    """
    importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    print("\nTop Feature Importances:")
    print(importance_df.head(20))

    mlflow.log_table(importance_df, "feature_importance.json")


# ============================================================
# Main training workflow
# ============================================================


def main() -> None:
    """
    Train and evaluate the LightGBM benchmark using rolling backtesting.
    """
    # ------------------------------------------------------------
    # Configure runtime
    # ------------------------------------------------------------
    config = LightGBMTrainingConfig()


    backtest_config = RollingBacktestConfig(
        horizon_days=config.horizon_days,
        n_windows=config.n_windows,
        target_column="sales",
        date_column="date",
    )

    configure_mlflow()
    print(f"MLflow tracking URI: {get_mlflow_tracking_uri()}")
    mlflow.set_experiment(config.experiment_name)

    # ------------------------------------------------------------
    # Load dataset
    # ------------------------------------------------------------
    # if config.limit_series is None:
    #     df = load_modeling_dataset_from_s3("ml/training_extracts/full")
    # else:
    #     df = load_top_series_subset(limit_series=config.limit_series)

    df = load_modeling_dataset_from_s3("ml/training_extracts/full")

    # ------------------------------------------------------------
    # Build features
    # ------------------------------------------------------------
    feature_df = build_features(df)

    modeling_df = prepare_modeling_dataset(
        feature_df,
        feature_set_name=config.feature_set_name,
    )

    feature_columns = get_feature_columns(config.feature_set_name)

    # ------------------------------------------------------------
    # Start MLflow run
    # ------------------------------------------------------------
    with mlflow.start_run(
        run_name=(
            f"lgbm_{config.feature_set_name}_"
            f"top{config.limit_series}_"
            f"h{config.horizon_days}_"
            f"w{config.n_windows}"
        )
    ):
        # --------------------------------------------------------
        # Log run configuration
        # --------------------------------------------------------
        mlflow.log_params(asdict(config))
        mlflow.log_param("feature_count", len(feature_columns))
        mlflow.log_param("feature_columns", ",".join(feature_columns))

        # --------------------------------------------------------
        # Run rolling backtesting
        # --------------------------------------------------------
        backtest_results_df = run_rolling_backtest(
            modeling_df=modeling_df,
            feature_columns=feature_columns,
            model_factory=lambda: build_model(config),
            config=backtest_config,
        )

        avg_wmape = float(backtest_results_df["wmape"].mean())
        avg_mae = float(backtest_results_df["mae"].mean())
        avg_rmse = float(backtest_results_df["rmse"].mean())

        # --------------------------------------------------------
        # Train final model on all available modeling data
        # --------------------------------------------------------
        final_model = build_model(config)
        final_model.fit(
            modeling_df[feature_columns],
            modeling_df["sales"],
        )

        # --------------------------------------------------------
        # Log explainability artifacts
        # --------------------------------------------------------
        log_feature_importance(final_model, feature_columns)

        # --------------------------------------------------------
        # Log model artifact
        # --------------------------------------------------------
        mlflow.lightgbm.log_model(
            final_model,
            artifact_path="model",
            registered_model_name=get_lightgbm_registered_model_name(),
        )

        # --------------------------------------------------------
        # Log aggregate metrics
        # --------------------------------------------------------
        mlflow.log_metric("avg_wmape", avg_wmape)
        mlflow.log_metric("avg_mae", avg_mae)
        mlflow.log_metric("avg_rmse", avg_rmse)
        mlflow.log_metric("modeling_rows", len(modeling_df))
        mlflow.log_metric("backtest_windows", config.n_windows)

        # --------------------------------------------------------
        # Log per-window metrics
        # --------------------------------------------------------
        for _, row in backtest_results_df.iterrows():
            window = int(row["window"])
            mlflow.log_metric(f"wmape_window_{window}", float(row["wmape"]))
            mlflow.log_metric(f"mae_window_{window}", float(row["mae"]))
            mlflow.log_metric(f"rmse_window_{window}", float(row["rmse"]))

        # --------------------------------------------------------
        # Console summary
        # --------------------------------------------------------
        print("LightGBM rolling backtest complete.")
        print(f"Experiment: {config.experiment_name}")
        print(f"Feature set: {config.feature_set_name}")
        print(f"Modeling rows: {len(modeling_df):,}")
        print(f"Average WMAPE: {avg_wmape:.4f}")
        print(f"Average MAE: {avg_mae:.4f}")
        print(f"Average RMSE: {avg_rmse:.4f}")
        print()
        print(backtest_results_df)


if __name__ == "__main__":
    main()