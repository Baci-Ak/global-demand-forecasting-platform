FROM ghcr.io/mlflow/mlflow:v2.14.3

# Add database + S3 dependencies needed for Postgres backend + S3/MinIO artifacts
RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    boto3==1.34.162
