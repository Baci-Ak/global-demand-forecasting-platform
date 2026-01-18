from dataclasses import dataclass
import os
from dotenv import load_dotenv
import subprocess
from pathlib import Path
import zipfile


load_dotenv()

@dataclass(frozen=True)
class KaggleConfig:
    username: str
    api_token: str
    dataset_name: str
    destination: str


def load_kaggle_config() -> KaggleConfig:
    username = os.getenv("KAGGLE_USERNAME")
    token = os.getenv("KAGGLE_API_TOKEN")
    dataset = os.getenv("M5_COMPETITION", "m5-forecasting-accuracy")
    destination = os.getenv("M5_DESTINATION", "local_data/m5")

    if not username or not token:
        raise RuntimeError("KAGGLE_USERNAME or KAGGLE_API_TOKEN is not set in .env")

    return KaggleConfig(
        username=username,
        api_token=token,
        dataset_name=dataset,
        destination=destination,
    )


def kaggle_smoke_test() -> None:
    """
    Verifies Kaggle API auth by listing datasets using the shell.
    """
    load_kaggle_config()
    result = subprocess.run(
        ["kaggle", "datasets", "list", "--max-size", "1"],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout.splitlines()[0])


def download_dataset() -> str:
    """
    Downloads M5 competition files using Kaggle CLI (env-token auth),
    then unzips into the destination folder.
    Returns the path where files were saved.
    """
    config = load_kaggle_config()
    os.makedirs(config.destination, exist_ok=True)

    # Use Kaggle CLI because it supports env-token auth cleanly (KAGGLE_API_TOKEN)
    subprocess.run(
        [
            "kaggle",
            "competitions",
            "download",
            "-c",
            config.dataset_name,
            "-p",
            config.destination,
            "--force",
        ],
        check=True,
    )

    # unzip the competition bundle
    zip_path = Path(config.destination) / f"{config.dataset_name}.zip"
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(config.destination)
    zip_path.unlink(missing_ok=True)

    print(f"Competition {config.dataset_name} downloaded to {config.destination}")
    return config.destination


