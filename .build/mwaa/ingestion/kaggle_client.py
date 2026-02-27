"""
Kaggle client utilities.

This module wraps the Kaggle CLI to:
- validate Kaggle authentication
- download and extract a configured competition dataset (e.g., M5)
"""

from __future__ import annotations

import os
import io
import subprocess
import zipfile
from pathlib import Path
from typing import Dict
import tempfile

from app_config.config import settings
from ingestion.s3_client import upload_fileobj_to_bronze


def _require_kaggle_credentials() -> None:
    """
    Ensure Kaggle credentials are available via Settings.
    """
    if not settings.KAGGLE_USERNAME or not settings.KAGGLE_API_TOKEN:
        raise RuntimeError(
            "Missing Kaggle credentials. Set KAGGLE_USERNAME and KAGGLE_API_TOKEN."
        )


def _kaggle_env() -> Dict[str, str]:
    """
    Build environment variables for Kaggle CLI subprocess calls.

    Kaggle CLI commonly expects:
    - KAGGLE_USERNAME
    - KAGGLE_KEY
    """
    _require_kaggle_credentials()

    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = settings.KAGGLE_USERNAME  
    env["KAGGLE_KEY"] = settings.KAGGLE_API_TOKEN     

    env["KAGGLE_API_TOKEN"] = settings.KAGGLE_API_TOKEN  
    return env


def kaggle_smoke_test() -> None:
    """
    Validate Kaggle CLI authentication by running a lightweight listing command.
    """
    result = subprocess.run(
        ["kaggle", "datasets", "list", "--max-size", "1"],
        capture_output=True,
        text=True,
        check=True,
        env=_kaggle_env(),
    )

    lines = result.stdout.splitlines()
    if lines:
        print(lines[0])


def download_dataset() -> str:
    """
    Download and extract the Kaggle competition dataset configured in Settings.

    Uses:
    - M5_COMPETITION: competition slug (default: "m5-forecasting-accuracy")
    - M5_DESTINATION: destination directory (default: "local_data/m5")

    Returns:
        Destination directory path (string).
    """
    competition = settings.M5_COMPETITION or "m5-forecasting-accuracy"
    destination = Path(settings.M5_DESTINATION or "local_data/m5")
    destination.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "kaggle",
            "competitions",
            "download",
            "-c",
            competition,
            "-p",
            str(destination),
            "--force",
        ],
        check=True,
        env=_kaggle_env(),
    )

    zip_path = destination / f"{competition}.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(destination)
        zip_path.unlink(missing_ok=True)

    print(f"Competition {competition} downloaded to {destination}")
    return str(destination)




def download_competition_zip_to_bronze(*, s3_key: str) -> str:
    """
    Download the Kaggle competition ZIP to an ephemeral temp directory and upload to Bronze.

    This avoids any persistent local staging like `local_data/m5` while staying compatible
    with the Kaggle CLI (which is not reliably stdout-streamable for competitions).
    """
    competition = settings.M5_COMPETITION or "m5-forecasting-accuracy"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        subprocess.run(
            [
                "kaggle",
                "competitions",
                "download",
                "-c",
                competition,
                "-p",
                str(tmpdir_path),
                "--force",
            ],
            check=True,
            env=_kaggle_env(),
        )

        zip_path = tmpdir_path / f"{competition}.zip"
        if not zip_path.exists():
            raise RuntimeError(f"Expected Kaggle zip not found at: {zip_path}")

        # Upload the zip to Bronze using streaming fileobj
        with zip_path.open("rb") as f:
            return upload_fileobj_to_bronze(f, s3_key)
