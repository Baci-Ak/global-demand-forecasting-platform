#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <old_tfstate_bucket> <new_tfstate_bucket>"
  exit 1
fi

OLD_BUCKET="$1"
NEW_BUCKET="$2"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Updating Terraform backend bucket references..."
echo "Old: ${OLD_BUCKET}"
echo "New: ${NEW_BUCKET}"
echo "Root: ${ROOT_DIR}"

grep -RIl --exclude-dir=".terraform" --exclude="*.tfstate" --exclude="*.tfstate.backup" "${OLD_BUCKET}" "${ROOT_DIR}" | while read -r file; do
  echo "Updating ${file}"
  sed -i.bak "s/${OLD_BUCKET}/${NEW_BUCKET}/g" "${file}"
  rm -f "${file}.bak"
done

echo "Done."