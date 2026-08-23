#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f vendor/chummer/data/metatypes.xml ]; then
  python3 scripts/fetch_chummer_data.py
fi
exec python3 -m uvicorn app.main:app --reload --app-dir . --host 127.0.0.1 --port 8000
