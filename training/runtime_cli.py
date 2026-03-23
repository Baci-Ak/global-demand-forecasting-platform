"""
training.runtime_cli

Production command-line interface for the ML runtime container.

Purpose
-------
Provide a single entrypoint that exposes supported runtime commands
for the ML container. This allows the container to run different tasks
in ECS, Airflow, MWAA, or local Docker using simple commands.

Example usage
-------------

docker run gdf-ml-runtime train-lightgbm
docker run gdf-ml-runtime train-random-forest
docker run gdf-ml-runtime predict-next-28-days
docker run gdf-ml-runtime export-training-extract
docker run gdf-ml-runtime smoke-test
"""

from __future__ import annotations

import argparse
import sys


# ------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------

def run_train_lightgbm() -> None:
    from training.models.train_lightgbm import main
    main()


def run_train_random_forest() -> None:
    from training.models.train_random_forest import main
    main()


def run_predict_next_28_days() -> None:
    from training.prediction.predict_next_28_days import main
    main()


def run_export_training_extract() -> None:
    from training.data_extract.unload_training_extract import main
    main()


def run_smoke_test() -> None:
    from training.tests.smoke_runtime_imports import main
    main()


# ------------------------------------------------------------
# CLI definition
# ------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdf-ml-runtime",
        description="Global Demand Forecasting ML runtime CLI",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("train-lightgbm")
    sub.add_parser("train-random-forest")
    sub.add_parser("predict-next-28-days")
    sub.add_parser("export-training-extract")
    sub.add_parser("smoke-test")

    return parser


# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command

    if command == "train-lightgbm":
        run_train_lightgbm()

    elif command == "train-random-forest":
        run_train_random_forest()

    elif command == "predict-next-28-days":
        run_predict_next_28_days()

    elif command == "export-training-extract":
        run_export_training_extract()

    elif command == "smoke-test":
        run_smoke_test()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()