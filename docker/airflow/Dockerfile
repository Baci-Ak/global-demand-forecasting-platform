# ------------------------------------------------------------------------------
# docker/airflow/Dockerfile
#

# ------------------------------------------------------------------------------

FROM apache/airflow:2.9.3

USER root

# System deps (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    build-essential \
    libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*


# Return to the airflow user (best practice)
USER airflow

# Python deps for DAG tasks
COPY docker/airflow/requirements-airflow.txt /opt/airflow/requirements-airflow.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements-airflow.txt


