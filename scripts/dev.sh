#!/usr/bin/env bash
# Run the backend (autoreload :8000) and the Next dev server (:3000) together.
# Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")/.."

# A virtualenv puts its entry points in `bin/` on POSIX and in `Scripts/` on
# Windows, where they also carry `.exe`. Pick whichever is actually there, so
# this runs from Git Bash / WSL on a Windows checkout as well.
if [ -x backend/.venv/Scripts/python.exe ]; then
  VENV=.venv/Scripts
elif [ -x backend/.venv/bin/python ]; then
  VENV=.venv/bin
else
  echo "backend/.venv missing — run 'make setup' first" >&2
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "frontend/node_modules missing — run 'make setup' first" >&2
  exit 1
fi
if [ ! -f backend/vendor/chummer/data/metatypes.xml ]; then
  echo "→ fetching Chummer data (one-off)"
  (cd backend && "./$VENV/python" scripts/fetch_chummer_data.py)
fi

trap 'kill 0' EXIT INT TERM
(cd backend && exec "./$VENV/uvicorn" app.main:app --reload --host 127.0.0.1 --port 8000) &
(cd frontend && exec npm run dev) &
wait
