"""create staging schema

Revision ID: 8aa6a32eb5f5
Revises: 52217c8d714d
Create Date: 2026-01-22 14:07:15.768077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from config.config import settings


# revision identifiers, used by Alembic.
revision: str = '8aa6a32eb5f5'
down_revision: Union[str, Sequence[str], None] = '52217c8d714d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a dedicated schema for raw-loaded tables from Bronze (S3/MinIO).
    # dbt will read from staging.* and build curated models into warehouse.*.
    op.execute(f'CREATE SCHEMA IF NOT EXISTS {settings.STAGING_SCHEMA};')


def downgrade() -> None:
    """Downgrade schema."""
    # Local-dev convenience: drop staging schema and everything in it.
    # In production you might not want to drop schemas automatically.
    op.execute('DROP SCHEMA IF EXISTS {settings.STAGING_SCHEMA} CASCADE;')
