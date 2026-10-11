#!/usr/bin/env bash
# Chummer's defaults; all publication state and control flow live in publish.sh.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
exec bash "$root/scripts/publish.sh" \
  --ci-workflow ci.yml \
  --deploy-workflow deploy-cloudrun.yml \
  --deploy-input image \
  --artifact-pattern 'signing (ghcr\.io/kenken-trpg/chummer-web@sha256:[0-9a-f]{64})' \
  --preflight '[[ $(gh repo view --json nameWithOwner --jq .nameWithOwner) == kenken-trpg/chummer-web ]] && python3 scripts/changelog.py check-pr "$PUBLISH_BASE" "$PUBLISH_TITLE"' \
  --verify-command 'bash scripts/verify-public.sh https://chummer-web.millionskenken.org' \
  "$@"
