#!/usr/bin/env bash
# Exit 2 distinguishes a Cloudflare challenge from a failed application probe.
set -euo pipefail
[[ $# == 1 ]] || { echo 'Usage: scripts/verify-public.sh PUBLIC_URL' >&2; exit 1; }
base=${1%/}
probe_dir=$(mktemp -d)
trap 'rm -f "$probe_dir/headers" "$probe_dir/body"; rmdir "$probe_dir"' EXIT
result=0
for path in /api/ready /; do
  echo "GET $base$path"
  code=$(curl -sS --max-time 20 -D "$probe_dir/headers" -o "$probe_dir/body" -w '%{http_code}' "$base$path") || exit 1
  if python3 - "$probe_dir/headers" <<'PY'
import sys
with open(sys.argv[1]) as f:
    challenged = any(line.strip().lower() == 'cf-mitigated: challenge' for line in f)
sys.exit(0 if challenged else 1)
PY
  then
    echo 'Cloudflare challenge: public verification incomplete'
    result=2
    continue
  fi
  [[ $code == 200 ]] || { echo "Unexpected HTTP status: $code" >&2; exit 1; }
  python3 - "$path" "$probe_dir/body" <<'PY'
import json, sys
with open(sys.argv[2]) as f:
    body = f.read()
valid = json.loads(body).get('ready') is True if sys.argv[1] == '/api/ready' else '<html' in body.lower()
sys.exit(0 if valid else 'Unexpected public response content')
PY
done
exit "$result"
