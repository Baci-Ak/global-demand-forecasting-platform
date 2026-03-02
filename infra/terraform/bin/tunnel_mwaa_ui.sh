#!/usr/bin/env bash
set -euo pipefail

# Load local config (not committed)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:?Set ENVIRONMENT in infra/terraform/bin/.env}"
LOCAL_MWAA_UI_PORT="${LOCAL_MWAA_UI_PORT:-8080}"

# Source of truth: terraform outputs (no hardcoding; works dev/prod)
JUMPHOST_INSTANCE_ID="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/ssm-jumphost output -raw jumphost_instance_id
)"

MWAA_HOST="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/mwaa output -raw mwaa_webserver_url
)"

# In case output includes https://
MWAA_HOST="${MWAA_HOST#https://}"
MWAA_HOST="${MWAA_HOST%/}"

echo "Starting SSM tunnel to MWAA Webserver (PRIVATE_ONLY)..."
echo "  Jump host:  ${JUMPHOST_INSTANCE_ID}"
echo "  MWAA host:  ${MWAA_HOST}:443"
echo "  Local:      127.0.0.1:${LOCAL_MWAA_UI_PORT}"
echo
echo "IMPORTANT (one-time per machine): map MWAA hostname to localhost while tunnel is open:"
echo "  sudo sh -c 'echo \"127.0.0.1 ${MWAA_HOST}\" >> /etc/hosts'"
echo
echo "Then open in a browser:"
echo "  https://${MWAA_HOST}:${LOCAL_MWAA_UI_PORT}/"
echo
echo "Keep this terminal open while using the UI."

aws ssm start-session \
  --region "${AWS_REGION}" \
  --target "${JUMPHOST_INSTANCE_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${MWAA_HOST}\"],\"portNumber\":[\"443\"],\"localPortNumber\":[\"${LOCAL_MWAA_UI_PORT}\"]}"