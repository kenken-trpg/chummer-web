#!/bin/zsh
# Regenerate the Japanese translation artifacts from the curated source of truth.
#
#   data/ja_overrides/data.json        <- import_ja_from_refs.py
#   docs/translation-import-report.md  <- import_ja_from_refs.py --write
#   docs/translation-glossary*.md      <- build_ja_glossary.py
#
# data.json is a *generated* file: all entries come from the curated modules
# (import_ja_from_refs.CURATED, ja_curated_spells.SPELLS, ja_curated_entities.ENTITIES)
# plus exact-name matches from the external reference material. To add or fix a
# translation, edit those modules, not data.json — this script resets and rebuilds
# it so the file stays deterministic.
#
# ui.json is hand-maintained and is NOT touched here.
#
# Reference material lives outside the repo; point $JA_REF_DIR at it (defaults
# to ~/Downloads). The scripts degrade gracefully when a file is missing
# (see their --help).
#
# Usage:  backend/scripts/regen_ja.sh [--no-reset] [--no-test]
#   --no-reset : keep existing data.json entries (additive import only)
#   --no-test  : skip the translation test run at the end

set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
fi

reset=1
run_test=1
for arg in "$@"; do
  case "$arg" in
    --no-reset) reset=0 ;;
    --no-test)  run_test=0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [ "$reset" -eq 1 ]; then
  echo "→ reset data/ja_overrides/data.json"
  printf '{\n}\n' > data/ja_overrides/data.json
fi

echo "→ import_ja_from_refs.py --write"
"$PY" scripts/import_ja_from_refs.py --write

echo "→ build_ja_glossary.py"
"$PY" scripts/build_ja_glossary.py

if [ "$run_test" -eq 1 ]; then
  echo "→ pytest (translation)"
  "$PY" -m pytest -q tests/test_translation_overrides.py tests/test_terminology.py
fi

echo
echo "✓ done — review:"
echo "    git diff -- backend/data/ja_overrides/data.json docs/translation-*.md"
