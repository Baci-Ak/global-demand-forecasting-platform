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
LOCAL_REDSHIFT_PORT="${LOCAL_REDSHIFT_PORT:-5439}"

# Source of truth: terraform outputs (no hardcoding, works dev/prod)
JUMPHOST_INSTANCE_ID="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/ssm-jumphost output -raw jumphost_instance_id
)"

REDSHIFT_HOST="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/redshift output -raw endpoint
)"

REDSHIFT_PORT="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/redshift output -raw port
)"

echo "Starting SSM tunnel to Redshift..."
echo "  Jump host:  ${JUMPHOST_INSTANCE_ID}"
echo "  Remote:     ${REDSHIFT_HOST}:${REDSHIFT_PORT}"
echo "  Local:      localhost:${LOCAL_REDSHIFT_PORT}"
echo "Keep this terminal open while connected."

aws ssm start-session \
  --region "${AWS_REGION}" \
  --target "${JUMPHOST_INSTANCE_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${REDSHIFT_HOST}\"],\"portNumber\":[\"${REDSHIFT_PORT}\"],\"localPortNumber\":[\"${LOCAL_REDSHIFT_PORT}\"]}"
