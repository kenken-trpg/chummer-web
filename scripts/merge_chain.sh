#!/usr/bin/env bash
# Rebase, check and merge a queue of PRs, one after another.
#
#   scripts/merge_chain.sh 248:feat/help-avail-grade 249:feat/help-bonus-sources
#
# Each PR is rebased onto the current origin/main (so the one before it is
# already in), checked the way CI checks it, pushed, and merged once GitHub's
# checks pass. A conflict in CHANGELOG.md or a test file keeps both sides —
# two entries or two test cases are what the two branches meant. Any other
# conflict stops the run for a human. The run ends on main, up to date.
set -u
cd "$(dirname "$0")/.."
here=$(pwd)
keepboth=scripts/keep_both_sides.py

for pair in "$@"; do
  n=${pair%%:*}; br=${pair#*:}
  echo "=== #$n $br"
  if [ "$(gh pr view "$n" --json state -q .state)" = MERGED ]; then echo "already merged"; continue; fi
  git fetch -q origin
  git switch -q "$br" || exit 1
  if ! git rebase origin/main >/dev/null 2>&1; then
    while true; do
      files=$(git diff --name-only --diff-filter=U)
      [ -z "$files" ] && break
      for f in $files; do
        case "$f" in
          CHANGELOG.md|*/tests/*|*.test.ts|*.test.tsx) python3 "$keepboth" "$f" || exit 1 ;;
          *) echo "STOP: conflict in $f"; exit 1 ;;
        esac
        if grep -q '^<<<<<<<\|^>>>>>>>' "$f"; then echo "STOP: markers left in $f"; exit 1; fi
        git add "$f"
      done
      GIT_EDITOR=true git rebase --continue >/dev/null 2>&1 || true
      git status | grep -q "rebase in progress" || break
    done
  fi
  (cd backend && uv run --no-sync ruff format -q tests && uv run --no-sync ruff check -q app tests &&
    uv run --no-sync pytest -q 2>&1 | tail -1) || { echo "STOP: backend checks"; exit 1; }
  if git diff --name-only origin/main | grep -q '^frontend/'; then
    (cd frontend && npx prettier --write --log-level warn . >/dev/null &&
      npx tsc --noEmit && npx vitest run 2>&1 | grep -E "Tests ") || { echo "STOP: frontend checks"; exit 1; }
  fi
  # Formatting the tree is part of the checks above, so a rebase that left a
  # file unformatted gets its own commit rather than a dirty tree at push.
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    git commit -qam "style: format after rebase"
  fi
  git push -q --force-with-lease origin "$br" || exit 1
  sleep 30  # let GitHub register the push before watching its checks
  gh pr checks "$n" --watch >/dev/null 2>&1
  bad=$(gh pr checks "$n" | grep -v -E "\bpass\b|skipping")
  if [ -n "$bad" ]; then echo "STOP: checks"; echo "$bad"; exit 1; fi
  gh pr merge "$n" --squash --delete-branch >/dev/null 2>&1 || { echo "STOP: merge failed"; exit 1; }
  echo "merged #$n"
done
cd "$here" && git switch -q main && git pull -q --ff-only && echo DONE
