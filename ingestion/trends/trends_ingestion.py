"""
Module: ingestion.trends.trends_ingestion

Purpose
-------
Ingest Google Trends interest-over-time data into the Bronze layer.

Pattern
-------
1) create audit.ingestion_runs row
2) extract raw payloads from provider
3) write raw artifacts to Bronze
4) mark audit row SUCCEEDED or FAILED
"""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO, StringIO
import time

import pandas as pd
from pytrends.exceptions import TooManyRequestsError
from sqlalchemy import text

from app_config.config import settings
from audit_log.ingestion_audit_logger import fail_run, start_run, succeed_run
from database.database import AuditSessionLocal, warehouse_engine
from ingestion.s3_client import upload_fileobj_to_bronze
from ingestion.trends.bronze_keys import build_trends_bronze_key
from ingestion.trends.extract_google_trends import (
    fetch_interest_over_time,
    make_trend_client,
)
from ingestion.trends.keywords_registry import TRENDS_KEYWORDS
from ingestion.trends.provider_contract import SCHEMA_VERSION, SOURCE_NAME


# ------------------------------------------------------------------------------
# Tunables
# ------------------------------------------------------------------------------
# Chunk the full historical window so Google Trends requests stay reasonably small.
TRENDS_CHUNK_DAYS = 180

# Retry settings for a single chunk.
TRENDS_MAX_RETRIES_PER_CHUNK = 6
TRENDS_BASE_SLEEP_SECONDS = 20

# Cooldowns to reduce provider throttling.
TRENDS_SLEEP_BETWEEN_CHUNKS_SECONDS = 8
TRENDS_SLEEP_BETWEEN_KEYWORDS_SECONDS = 45

# If a single keyword keeps getting throttled, rebuild the TrendReq session and retry.
TRENDS_MAX_SESSION_RESETS_PER_KEYWORD = 2


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _get_m5_sales_date_range() -> tuple[date, date]:
    """
    Read the M5 sales date range from staged M5 data, not Silver.

    Why:
    - External-source Bronze ingestion must be bootstrap-safe.
    - Silver may not exist yet on a clean rebuild.
    - M5 staging is guaranteed to exist before external ingestion runs.
    """
    sql = text(
        """
        select
            min(cast(c.date as date)) as min_date,
            max(cast(c.date as date)) as max_date
        from staging.m5_sales_train_validation_long_raw s
        join staging.m5_calendar_raw c
          on s.d = c.d
        """
    )

    with warehouse_engine.begin() as conn:
        row = conn.execute(sql).mappings().one()

    min_date = row["min_date"]
    max_date = row["max_date"]

    if min_date is None or max_date is None:
        raise RuntimeError(
            "Could not determine M5 sales date range from staging M5 tables."
        )

    return min_date, max_date


def _build_date_chunks(
    *,
    start_date: date,
    end_date: date,
    chunk_days: int = TRENDS_CHUNK_DAYS,
) -> list[tuple[date, date]]:
    """
    Split a large inclusive date range into smaller inclusive chunks.
    """
    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date")

    chunks: list[tuple[date, date]] = []
    chunk_start = start_date

    while chunk_start <= end_date:
        chunk_end = min(chunk_start + timedelta(days=chunk_days - 1), end_date)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + timedelta(days=1)

    return chunks


def _sleep_with_backoff(attempt: int) -> None:
    """
    Sleep using increasing backoff to reduce repeated 429 throttling.
    """
    sleep_seconds = TRENDS_BASE_SLEEP_SECONDS * attempt
    time.sleep(sleep_seconds)


def _fetch_interest_over_time_chunked(
    *,
    keyword: str,
    start_date: date,
    end_date: date,
    geo: str | None = None,
) -> pd.DataFrame:
    """
    Fetch Google Trends over the full requested period by chunking the date range
    into smaller windows and retrying each chunk with backoff.

    Operational behavior
    --------------------
    - Reuses one TrendReq session across the keyword where possible.
    - If repeated 429s occur, rebuilds the session and retries.
    - Preserves full history by stitching chunk results back together.
    """
    chunks = _build_date_chunks(start_date=start_date, end_date=end_date)
    frames: list[pd.DataFrame] = []

    pytrends = make_trend_client()
    session_reset_count = 0

    for idx, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        chunk_completed = False

        for attempt in range(1, TRENDS_MAX_RETRIES_PER_CHUNK + 1):
            try:
                df = fetch_interest_over_time(
                    pytrends=pytrends,
                    keyword=keyword,
                    start_date=chunk_start,
                    end_date=chunk_end,
                    geo=geo,
                )

                if df.empty:
                    raise RuntimeError(
                        f"No Google Trends data returned for keyword={keyword} "
                        f"chunk={chunk_start}..{chunk_end}"
                    )

                frames.append(df)

                print(
                    f"Fetched Trends chunk {idx}/{len(chunks)} for keyword={keyword} "
                    f"covering {chunk_start} -> {chunk_end} "
                    f"(rows={len(df)})"
                )

                chunk_completed = True
                break

            except TooManyRequestsError as e:
                if attempt == TRENDS_MAX_RETRIES_PER_CHUNK:
                    if session_reset_count < TRENDS_MAX_SESSION_RESETS_PER_KEYWORD:
                        session_reset_count += 1
                        pytrends = make_trend_client()
                        print(
                            f"Rebuilt Google Trends session for keyword={keyword} "
                            f"after repeated 429s on chunk {chunk_start} -> {chunk_end} "
                            f"(session_reset={session_reset_count}/{TRENDS_MAX_SESSION_RESETS_PER_KEYWORD})"
                        )
                        time.sleep(TRENDS_SLEEP_BETWEEN_KEYWORDS_SECONDS)
                        # restart retries for the same chunk using a fresh session
                        break

                    raise RuntimeError(
                        f"Failed to fetch Google Trends for keyword={keyword} "
                        f"chunk={chunk_start}..{chunk_end} after "
                        f"{TRENDS_MAX_RETRIES_PER_CHUNK} attempts and "
                        f"{TRENDS_MAX_SESSION_RESETS_PER_KEYWORD} session resets"
                    ) from e

                print(
                    f"Retrying Trends chunk for keyword={keyword} "
                    f"covering {chunk_start} -> {chunk_end} "
                    f"(attempt {attempt}/{TRENDS_MAX_RETRIES_PER_CHUNK}) "
                    f"due to 429 throttling"
                )
                _sleep_with_backoff(attempt)

            except Exception as e:
                if attempt == TRENDS_MAX_RETRIES_PER_CHUNK:
                    raise RuntimeError(
                        f"Failed to fetch Google Trends for keyword={keyword} "
                        f"chunk={chunk_start}..{chunk_end} after "
                        f"{TRENDS_MAX_RETRIES_PER_CHUNK} attempts"
                    ) from e

                print(
                    f"Retrying Trends chunk for keyword={keyword} "
                    f"covering {chunk_start} -> {chunk_end} "
                    f"(attempt {attempt}/{TRENDS_MAX_RETRIES_PER_CHUNK}, "
                    f"error={type(e).__name__}: {e})"
                )
                _sleep_with_backoff(attempt)

        # If the chunk was not completed and we rebuilt session, retry the same chunk
        # with the fresh session before moving on.
        if not chunk_completed:
            for attempt in range(1, TRENDS_MAX_RETRIES_PER_CHUNK + 1):
                try:
                    df = fetch_interest_over_time(
                        pytrends=pytrends,
                        keyword=keyword,
                        start_date=chunk_start,
                        end_date=chunk_end,
                        geo=geo,
                    )

                    if df.empty:
                        raise RuntimeError(
                            f"No Google Trends data returned for keyword={keyword} "
                            f"chunk={chunk_start}..{chunk_end}"
                        )

                    frames.append(df)

                    print(
                        f"Fetched Trends chunk {idx}/{len(chunks)} for keyword={keyword} "
                        f"covering {chunk_start} -> {chunk_end} after session reset "
                        f"(rows={len(df)})"
                    )

                    chunk_completed = True
                    break

                except Exception as e:
                    if attempt == TRENDS_MAX_RETRIES_PER_CHUNK:
                        raise RuntimeError(
                            f"Failed to fetch Google Trends for keyword={keyword} "
                            f"chunk={chunk_start}..{chunk_end} even after session reset"
                        ) from e

                    print(
                        f"Retrying Trends chunk after session reset for keyword={keyword} "
                        f"covering {chunk_start} -> {chunk_end} "
                        f"(attempt {attempt}/{TRENDS_MAX_RETRIES_PER_CHUNK}, "
                        f"error={type(e).__name__}: {e})"
                    )
                    _sleep_with_backoff(attempt)

        if not chunk_completed:
            raise RuntimeError(
                f"Chunk fetch never completed for keyword={keyword} "
                f"chunk={chunk_start}..{chunk_end}"
            )

        if idx < len(chunks):
            time.sleep(TRENDS_SLEEP_BETWEEN_CHUNKS_SECONDS)

    if not frames:
        raise RuntimeError(
            f"No Google Trends data fetched for keyword={keyword} "
            f"covering {start_date} -> {end_date}"
        )

    combined = pd.concat(frames, ignore_index=True)

    if "date" not in combined.columns:
        raise RuntimeError(
            f"Expected Trends payload to contain a 'date' column for keyword={keyword}. "
            f"Found columns={list(combined.columns)}"
        )

    combined["date"] = pd.to_datetime(combined["date"]).dt.date
    combined = combined.sort_values("date")
    combined = combined.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

    return combined


# ------------------------------------------------------------------------------
# Public ingestion entrypoint
# ------------------------------------------------------------------------------
def ingest_trends_to_bronze() -> None:
    """
    Run one Trends ingestion cycle and land raw CSV payloads in Bronze.
    """
    today = date.today()
    source_name = settings.TRENDS_SOURCE_NAME or SOURCE_NAME
    bronze_bucket = settings.BRONZE_BUCKET or ""

    if not bronze_bucket:
        raise RuntimeError("BRONZE_BUCKET is not configured.")

    db = AuditSessionLocal()
    run_id = None

    try:
        start_date, end_date = _get_m5_sales_date_range()

        run_id = start_run(
            db=db,
            source_name=source_name,
            ingest_date=today,
            schema_version=SCHEMA_VERSION,
        )
        db.commit()

        file_count = 0
        total_bytes = 0

        for idx, entry in enumerate(TRENDS_KEYWORDS, start=1):
            df = _fetch_interest_over_time_chunked(
                keyword=entry["keyword"],
                start_date=start_date,
                end_date=end_date,
                geo=entry["geo"],
            )

            df["keyword"] = entry["keyword"]
            df["feature_name"] = entry["feature_name"]
            df["label"] = entry["label"]
            df["geo"] = entry["geo"]
            df["source_name"] = source_name
            df["provider"] = settings.TRENDS_PROVIDER or "google_trends"
            df["schema_version"] = SCHEMA_VERSION
            df["ingest_date"] = today.isoformat()

            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)

            body = csv_buffer.getvalue().encode("utf-8")
            binary_buffer = BytesIO(body)

            s3_key = build_trends_bronze_key(
                ingest_date=today.isoformat(),
                keyword=entry["keyword"],
            )

            upload_fileobj_to_bronze(binary_buffer, s3_key)

            file_count += 1
            total_bytes += len(body)

            print(
                f"Uploaded Trends keyword {entry['keyword']} "
                f"covering {start_date} -> {end_date} "
                f"to s3://{bronze_bucket}/{s3_key}"
            )

            if idx < len(TRENDS_KEYWORDS):
                time.sleep(TRENDS_SLEEP_BETWEEN_KEYWORDS_SECONDS)

        succeed_run(
            db=db,
            run_id=run_id,
            s3_path=f"s3://{bronze_bucket}/source={source_name}/ingest_date={today.isoformat()}/",
            row_count=None,
            file_count=file_count,
            total_bytes=total_bytes,
        )
        db.commit()

        print(
            f"Trends ingestion run {run_id} SUCCEEDED "
            f"(file_count={file_count}, total_bytes={total_bytes})"
        )

    except Exception as e:
        db.rollback()

        if run_id is not None:
            try:
                fail_run(db=db, run_id=run_id, error_message=str(e))
                db.commit()
            except Exception:
                db.rollback()

        raise

    finally:
        db.close()