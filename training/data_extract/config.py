"""
training.data_extract.config

Configuration for production training extract generation.

Purpose
-------
- define the stable extract contract used by ECS training jobs
- keep production training bounded and repeatable
- separate extract sizing decisions from orchestration and model code

Design principles
-----------------
- keep configuration explicit and easy to reason about
- bound training scope to match current compute architecture
- allow future scale-up without changing downstream interfaces
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# Production training extract configuration
# ============================================================
# Purpose:
# - define how much history and how many series are exported
# - keep Layer 1 training within the current ECS memory envelope
# - provide one clear place to tune extract size
# ============================================================


@dataclass(frozen=True)
class TrainingExtractConfig:
    """
    Configuration for exporting the production training extract.
    """

    # Use recent history only for production retraining.
    training_history_days: int = 365

    # Keep the training universe bounded for the current ECS + pandas design.
    # This is a production constraint for Layer 1, not a notebook shortcut.
    limit_series: int | None = 500

    # Stable S3 location for the latest production training extract.
    s3_key_prefix: str = "ml/training_extracts/full"

    # Retained for compatibility, though Redshift UNLOAD performs the export.
    chunk_size: int = 25000