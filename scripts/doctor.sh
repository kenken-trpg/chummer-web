#!/usr/bin/env bash
# Preflight for a local self-host. Non-fatal — prints what to fix.
cd "$(dirname "$0")/.."
rc=0
good() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
bad()  { printf '  \033[33m✗\033[0m %s\n' "$1"; rc=1; }

echo "docker (the one-command path):"
if command -v docker >/dev/null 2>&1; then
  good "docker $(docker --version | awk '{print $3}' | tr -d ,)"
  docker compose version >/dev/null 2>&1 && good "docker compose" || bad "docker compose plugin not found"
else
  bad "docker not found — 'make up' needs it (or use the non-Docker path below)"
fi

echo "non-Docker path:"
if command -v python3 >/dev/null 2>&1; then
  v=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  case "$v" in 3.1[1-9] | 3.[2-9][0-9]) good "python $v" ;; *) bad "python $v — need >= 3.11" ;; esac
else
  bad "python3 not found"
fi
command -v node >/dev/null 2>&1 && good "node $(node -v)" || bad "node not found"
[ -x backend/.venv/bin/python ] && good "backend/.venv" || bad "backend/.venv missing — run 'make setup'"
[ -d frontend/node_modules ] && good "frontend/node_modules" || bad "frontend deps missing — run 'make setup'"
[ -f backend/vendor/chummer/data/metatypes.xml ] && good "Chummer data present" \
  || bad "Chummer data missing — run 'make data' (the Docker image bakes it in)"

echo "ports:"
for p in 8080 8000 3000; do
  if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
    bad "port $p is in use"
  else
    good "port $p free"
  fi
done

exit $rc
