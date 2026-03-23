# ==============================================================================
# docker/ml-runtime/Dockerfile
# ==============================================================================
#
# Purpose
# - Build the base container image for production ML runtime jobs on ECS.
# - Support running ML runtime commands through a single CLI entrypoint.
#
# Design principles
# - Keep the image narrow: copy only the code needed by ML jobs.
# - Keep runtime predictable: pin core Python dependencies in requirements.txt.
# - Install required OS libraries for native Python packages such as LightGBM.
# - Use one production CLI entrypoint for ECS / Airflow / MWAA.
# ==============================================================================

# ------------------------------------------------------------------------------
# Base runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim

# ------------------------------------------------------------------------------
# Application working directory
# ------------------------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------------------------
# System dependencies
# - libgomp1 is required by LightGBM at runtime.
# ------------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------------------
# Python dependency installation
# - Copy requirements first to maximize Docker layer caching.
# ------------------------------------------------------------------------------
COPY docker/ml-runtime/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# ------------------------------------------------------------------------------
# Application code
# - Copy only the ML runtime package.
# ------------------------------------------------------------------------------
COPY training /app/training

# ------------------------------------------------------------------------------
# Python import path
# ------------------------------------------------------------------------------
ENV PYTHONPATH=/app

# ------------------------------------------------------------------------------
# Container startup
# - All runtime commands flow through training.runtime_cli.
# - Default command is a container-safe smoke test.
# ------------------------------------------------------------------------------
ENTRYPOINT ["python", "-m", "training.runtime_cli"]
CMD ["smoke-test"]