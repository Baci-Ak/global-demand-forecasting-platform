#!/usr/bin/env bash
set -euo pipefail

# Load local config (not committed)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
TFSTATE_BUCKET="${TFSTATE_BUCKET:?Set TFSTATE_BUCKET in infra/terraform/bin/.env}"
ENVIRONMENT="${ENVIRONMENT:?Set ENVIRONMENT in infra/terraform/bin/.env}"
LOCAL_PORT="${LOCAL_PORT:-5432}"

# Read values from Terraform remote state (no hardcoding)
JUMPHOST_INSTANCE_ID="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/ssm-jumphost output -raw jumphost_instance_id
)"

RDS_HOST="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/rds-postgres output -raw endpoint
)"

RDS_PORT="$(
  terraform -chdir=infra/terraform/envs/${ENVIRONMENT}/rds-postgres output -raw port
)"

echo "Starting SSM tunnel to audit RDS..."
echo "  Jump host:  ${JUMPHOST_INSTANCE_ID}"
echo "  Remote DB:  ${RDS_HOST}:${RDS_PORT}"
echo "  Local:      localhost:${LOCAL_PORT}"
echo "Keep this terminal open while connected."

aws ssm start-session \
  --region "${AWS_REGION}" \
  --target "${JUMPHOST_INSTANCE_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${RDS_HOST}\"],\"portNumber\":[\"${RDS_PORT}\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}"
