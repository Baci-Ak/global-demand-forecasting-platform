#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Secret scan (lightweight)
#
# Purpose:
# - Prevent accidental commits of common secret patterns in tracked files.
# - This is NOT a replacement for a full secret scanner, but it's a strong
#   low-friction guardrail for this project.
#
# What it checks:
# - Looks for AWS Access Key IDs and suspicious long secret strings
# - Ensures `.env` is not tracked
#
# Exit codes:
# - 0: OK
# - 1: Potential secret found
# ------------------------------------------------------------------------------

set -euo pipefail

# 1) Ensure .env is not tracked
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "ERROR: .env is tracked by git. Remove it from git history and keep it untracked."
  exit 1
fi

# 2) Scan tracked files for AWS Access Key pattern
#    (AKIA / ASIA are common prefixes for access keys)
if git grep -nE '(AKIA|ASIA)[0-9A-Z]{16}' -- . ':!*.lock' >/dev/null 2>&1; then
  echo "ERROR: Potential AWS Access Key found in tracked files:"
  git grep -nE '(AKIA|ASIA)[0-9A-Z]{16}' -- . ':!*.lock'
  exit 1
fi

# 3) Scan for Kaggle token pattern (tokens start with KGAT_)
if git grep -nE 'KGAT_[0-9a-f]+' -- . ':!*.lock' >/dev/null 2>&1; then
  echo "ERROR: Potential Kaggle API token found in tracked files:"
  git grep -nE 'KGAT_[0-9a-f]+' -- . ':!*.lock'
  exit 1
fi

echo "✅ secret_scan OK"
