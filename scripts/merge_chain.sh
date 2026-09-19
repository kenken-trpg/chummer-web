#!/usr/bin/env bash
# Rebase, check and merge a queue of PRs, one after another.
#
#   scripts/merge_chain.sh 248:feat/help-avail-grade 249:feat/help-bonus-sources
#
# Each PR is rebased onto the current origin/main (so the one before it is
# already in), checked the way CI checks it, pushed, and handed to GitHub's
# auto-merge, which merges it when the required checks pass. The run waits for
# that merge anyway — the next PR rebases onto a main that contains this one.
#
# A conflict in CHANGELOG.md or a test file keeps both sides — two entries or
# two test cases are what the two branches meant. Any other
# conflict stops the run for a human — the i18n dictionaries included, even
# though two branches usually just append there: a conflicting wording is a
# choice, and a duplicated key would only surface in locales.test.ts. The run ends on main, up to date.
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
  sleep 20  # let GitHub register the push, so the checks below are this push's
  # GitHub merges it itself when the required checks pass. A required check that
  # has not reported yet blocks the merge, so enabling this before any check
  # appears cannot merge early.
  gh pr merge "$n" --squash --auto >/dev/null 2>&1 ||
    { echo "STOP: could not enable auto-merge"; exit 1; }
  # The queue still has to wait: the next PR is rebased onto a main that
  # contains this one. A failed check leaves the PR open forever, so this
  # watches for that as well as for the merge.
  state=
  for _ in $(seq 1 60); do
    state=$(gh pr view "$n" --json state -q .state)
    [ "$state" = MERGED ] && break
    bad=$(gh pr checks "$n" 2>/dev/null | grep -v -E "\bpass\b|\bpending\b|skipping")
    if [ -n "$bad" ]; then echo "STOP: checks"; echo "$bad"; exit 1; fi
    sleep 20
  done
  if [ "$state" != MERGED ]; then echo "STOP: still not merged after 20 min"; exit 1; fi
  # The remote branch goes with the repository's delete-on-merge setting; the
  # local one is ours to clean up, and cannot be deleted while checked out.
  git switch -q main && git branch -qD "$br"
  echo "merged #$n"
done
cd "$here" && git switch -q main && git pull -q --ff-only && echo DONE
