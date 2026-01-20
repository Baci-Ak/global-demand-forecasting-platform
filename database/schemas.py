from datetime import date, datetime
from uuid import UUID
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


DqRunStatus = Literal["STARTED", "PASSED", "FAILED"]
IngestionStatus = Literal["STARTED", "SUCCEEDED", "FAILED"]


# -----------------------
# dq_runs
# -----------------------

class DqRunBase(BaseModel):
    dataset_name: str
    suite_name: str
    status: DqRunStatus
    details_json: Optional[str] = None
    error_message: Optional[str] = None


class DqRunCreate(DqRunBase):
    pass


class DqRunUpdate(BaseModel):
    dataset_name: Optional[str] = None
    suite_name: Optional[str] = None
    status: Optional[DqRunStatus] = None
    details_json: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None 
    ended_at: Optional[datetime] = None


class DqRunRead(DqRunBase):
    model_config = ConfigDict(from_attributes=True)

    dq_run_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None


# -----------------------
# ingestion_runs
# -----------------------

class IngestionRunBase(BaseModel):
    source_name: str
    ingest_date: date
    status: IngestionStatus
    s3_path: Optional[str] = None
    row_count: Optional[int] = None
    schema_version: Optional[str] = None
    error_message: Optional[str] = None


class IngestionRunCreate(IngestionRunBase):
    pass


class IngestionRunUpdate(BaseModel):
    source_name: Optional[str] = None
    ingest_date: Optional[date] = None
    status: Optional[IngestionStatus] = None
    s3_path: Optional[str] = None
    row_count: Optional[int] = None
    schema_version: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None 
    ended_at: Optional[datetime] = None


class IngestionRunRead(IngestionRunBase):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
