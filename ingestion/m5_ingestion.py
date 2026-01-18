import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

from ingestion.s3_client import upload_file_to_bronze
from ingestion.audit_logger import start_run, succeed_run, fail_run
from ingestion.kaggle_client import download_dataset

load_dotenv()  # load .env variables

# Configuration
BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "demand-forecast-bronze")
DATA_DIR = Path(os.getenv("M5_DESTINATION", "local_data/m5"))  # local staging workspace
DATA_DIR.mkdir(parents=True, exist_ok=True)


def count_csv_rows(csv_path: Path) -> int:
    """
    Efficient row counter for CSVs:
    counts data rows only (excludes header) without loading file into memory.
    """
    with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
        return max(sum(1 for _ in f) - 1, 0)


def ingest_m5_to_bronze() -> None:
    """
    Production-grade ingestion:
    1) Create audit run (STARTED)
    2) Download M5 competition files into local staging (DATA_DIR)
    3) Upload CSVs to Bronze (MinIO/S3) with partitioned keys
    4) Mark audit run SUCCEEDED or FAILED
    """
    today = date.today()
    run_id = start_run(source_name="m5_sales", ingest_date=today)

    try:
        #  Download into local staging folder
        local_path = download_dataset()

        # Upload each CSV to Bronze + compute true row counts
        total_rows = 0
        for file_path in Path(local_path).glob("*.csv"):
            rows = count_csv_rows(file_path)
            total_rows += rows

            s3_key = f"source=m5_sales/ingest_date={today.isoformat()}/{file_path.name}"
            s3_url = upload_file_to_bronze(file_path, s3_key)
            print(f"Uploaded {file_path.name} ({rows} rows) → {s3_url}")

        # Mark success (row_count = total rows across all CSVs)
        succeed_run(
            run_id,
            s3_path=f"s3://{BRONZE_BUCKET}/source=m5_sales/ingest_date={today.isoformat()}/",
            row_count=total_rows,
        )
        print(f"Ingestion run {run_id} SUCCEEDED (total_rows={total_rows})")

    except Exception as e:
        # Mark failure and re-raise so Makefile shows the error
        fail_run(run_id, str(e))
        print(f"Ingestion run {run_id} FAILED: {e}")
        raise
