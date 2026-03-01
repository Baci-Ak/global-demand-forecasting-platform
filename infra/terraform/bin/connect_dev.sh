#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# connect_dev.sh
#
# Purpose
# - Open SSM tunnels (no public exposure) to private services:
#   - MWAA Web UI (443)
#   - RDS Postgres (5432)
#   - Redshift Serverless endpoint (5439)
#
# Requirements (on the user's laptop):
# - awscli + session-manager-plugin installed
# - AWS credentials to the target account
#
# Usage:
#   ./infra/terraform/bin/connect_dev.sh mwaa
#   ./infra/terraform/bin/connect_dev.sh postgres
#   ./infra/terraform/bin/connect_dev.sh redshift
#
# Optional env overrides:
#   AWS_REGION=us-east-1 ENVIRONMENT=dev LOCAL_PORT=8080 ./... mwaa
#   AWS_REGION=us-east-1 ENVIRONMENT=dev LOCAL_PORT=5432 ./... postgres
# ------------------------------------------------------------------------------

CMD="${1:-}"
if [[ -z "$CMD" ]]; then
  echo "Usage: $0 {mwaa|postgres|redshift}"
  exit 2
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCAL_PORT="${LOCAL_PORT:-}"

# ---- Parameter Store paths (standardized, non-secret) ----
P_BASE="/gdf/${ENVIRONMENT}"

P_JUMPHOST_ID="${P_BASE}/ssm/jumphost_instance_id"
P_MWAA_HOST="${P_BASE}/mwaa/webserver_host"
P_RDS_HOST="${P_BASE}/rds/endpoint_host"
P_RDS_PORT="${P_BASE}/rds/port"
P_REDSHIFT_HOST="${P_BASE}/redshift/endpoint_host"
P_REDSHIFT_PORT="${P_BASE}/redshift/port"

getp() {
  local name="$1"
  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "$name" \
    --query "Parameter.Value" \
    --output text
}

JUMPHOST_INSTANCE_ID="$(getp "$P_JUMPHOST_ID")"

start_tunnel() {
  local host="$1"
  local remote_port="$2"
  local local_port="$3"

  echo
  echo "Starting SSM port-forward:"
  echo "  env:        ${ENVIRONMENT}"
  echo "  region:     ${AWS_REGION}"
  echo "  jumphost:   ${JUMPHOST_INSTANCE_ID}"
  echo "  remote:     ${host}:${remote_port}"
  echo "  local:      127.0.0.1:${local_port}"
  echo
  echo "Keep this terminal open while you use the service."
  echo

  aws ssm start-session \
    --region "$AWS_REGION" \
    --target "$JUMPHOST_INSTANCE_ID" \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "{\"host\":[\"${host}\"],\"portNumber\":[\"${remote_port}\"],\"localPortNumber\":[\"${local_port}\"]}"
}

case "$CMD" in
    mwaa)
    MWAA_HOST="$(getp "$P_MWAA_HOST")"
    MWAA_HOST="${MWAA_HOST#https://}"
    MWAA_HOST="${MWAA_HOST%/}"
    LOCAL_PORT="${LOCAL_PORT:-8080}"

    echo
    echo "Open in your browser:"
    echo "  https://127.0.0.1:${LOCAL_PORT}/"
    echo "Keep this terminal open while using the UI."
    echo

    if ! grep -qE "^[#[:space:]]*127\.0\.0\.1[[:space:]]+${MWAA_HOST//./\\.}([[:space:]]|\$)" /etc/hosts; then
        echo "127.0.0.1 ${MWAA_HOST}" | sudo tee -a /etc/hosts >/dev/null
    fi
    echo "Open:"
    echo "  https://${MWAA_HOST}:${LOCAL_PORT}/"

    start_tunnel "$MWAA_HOST" "443" "$LOCAL_PORT"
    ;;

  postgres)
    RDS_HOST="$(getp "$P_RDS_HOST")"
    RDS_PORT="$(getp "$P_RDS_PORT")"
    LOCAL_PORT="${LOCAL_PORT:-5432}"

    echo "Then connect locally:"
    echo "  host=127.0.0.1 port=${LOCAL_PORT}"
    start_tunnel "$RDS_HOST" "$RDS_PORT" "$LOCAL_PORT"
    ;;

  redshift)
    RS_HOST="$(getp "$P_REDSHIFT_HOST")"
    RS_PORT="$(getp "$P_REDSHIFT_PORT")"
    LOCAL_PORT="${LOCAL_PORT:-5439}"

    echo "Then connect locally:"
    echo "  host=127.0.0.1 port=${LOCAL_PORT}"
    start_tunnel "$RS_HOST" "$RS_PORT" "$LOCAL_PORT"
    ;;

  *)
    echo "Unknown command: $CMD"
    echo "Usage: $0 {mwaa|postgres|redshift}"
    exit 2
    ;;
esac