#!/usr/bin/env bash
set -euo pipefail

# gdf-dev-connect-mwaa-mac.sh
# One-command MWAA UI access (PRIVATE_ONLY) on macOS via SSM tunnel.
#
# Requirements:
# - awscli + session-manager-plugin
# - IAM perms: ssm:GetParameter(s) on /gdf/dev/* and ssm:StartSession to jumphost
#
# Usage:
#   ./gdf-dev-connect-mwaa-mac.sh
#
# Optional:
#   AWS_REGION=us-east-1 ENVIRONMENT=dev ./gdf-dev-connect-mwaa-mac.sh

# If not root, re-run as root (needed to bind local port 443)
if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E "$0" "$@"
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
P_BASE="/gdf/${ENVIRONMENT}"

P_JUMPHOST_ID="${P_BASE}/ssm/jumphost_instance_id"
P_MWAA_HOST="${P_BASE}/mwaa/webserver_host"

getp() {
  local name="$1"
  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "$name" \
    --query "Parameter.Value" \
    --output text
}

JUMPHOST_INSTANCE_ID="$(getp "$P_JUMPHOST_ID")"
MWAA_HOST="$(getp "$P_MWAA_HOST")"
MWAA_HOST="${MWAA_HOST#https://}"
MWAA_HOST="${MWAA_HOST%/}"

# Ensure /etc/hosts mapping exists (idempotent)
if ! grep -qE "^[#[:space:]]*127\.0\.0\.1[[:space:]]+${MWAA_HOST//./\\.}([[:space:]]|\$)" /etc/hosts; then
  echo "Adding /etc/hosts mapping for MWAA host..."
  echo "127.0.0.1 ${MWAA_HOST}" | sudo tee -a /etc/hosts >/dev/null
else
  echo "/etc/hosts already contains mapping for ${MWAA_HOST}"
fi

# Flush macOS DNS
echo "Flushing DNS cache..."
sudo dscacheutil -flushcache || true
sudo killall -HUP mDNSResponder || true

echo
echo "Open Airflow UI:"
echo "  https://${MWAA_HOST}/"
echo
echo "Starting SSM tunnel (keep this terminal open)..."
echo "  region:   ${AWS_REGION}"
echo "  env:      ${ENVIRONMENT}"
echo "  jumphost: ${JUMPHOST_INSTANCE_ID}"
echo "  remote:   ${MWAA_HOST}:443"
echo "  local:    127.0.0.1:443"
echo

exec aws ssm start-session \
  --region "${AWS_REGION}" \
  --target "${JUMPHOST_INSTANCE_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${MWAA_HOST}\"],\"portNumber\":[\"443\"],\"localPortNumber\":[\"443\"]}"