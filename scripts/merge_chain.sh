#!/usr/bin/env bash
# Rebase, check and merge a queue of PRs, one after another.
#
#   scripts/merge_chain.sh 248:feat/help-avail-grade 249:feat/help-bonus-sources
#
# Each PR is rebased onto the current origin/main (so the one before it is
# already in), checked the way CI checks it, pushed, and — once *every* check
# on GitHub has reported green, not only the required ones — handed to
# auto-merge. The run waits for that merge anyway: the next PR rebases onto a
# main that contains this one.
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
  # Where this branch sat before the rebase, so that what main gained since can
  # be told apart from what the branch itself changes.
  was=$(git merge-base HEAD origin/main)
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
  # Which half to check. The point of checking at all is that main may have
  # moved under the branch, so it is not enough to ask what the branch changes:
  # both sides count. If neither touched a half, the green this PR already has
  # for it still stands and running it again buys nothing.
  #
  # Anything outside the two runs both, because what it reaches is not written
  # down anywhere this could read — scripts/ and the Makefile are what the
  # checks are invoked through. Prose is the exception, and it has to be: every
  # PR carries a changelog.d/ fragment, so counting those as `elsewhere` would
  # open both gates every time and this would decide nothing. A fragment,
  # a Markdown file, docs/ and .github/ cannot change what pytest or vitest do.
  touched=$( (git diff --name-only origin/main...HEAD; git diff --name-only "$was" origin/main) | sort -u)
  elsewhere=$(printf '%s\n' "$touched" |
    grep -vE '^(backend/|frontend/|changelog\.d/|docs/|\.github/|$)|\.md$')
  if [ -n "$elsewhere" ] || printf '%s\n' "$touched" | grep -q '^backend/'; then
    (cd backend && uv run --no-sync ruff format -q tests && uv run --no-sync ruff check -q app tests &&
      uv run --no-sync pytest -q -n auto 2>&1 | tail -1) || { echo "STOP: backend checks"; exit 1; }
  else
    echo "backend untouched on both sides — checked already"
  fi
  if [ -n "$elsewhere" ] || printf '%s\n' "$touched" | grep -q '^frontend/'; then
    (cd frontend && npx prettier --write --log-level warn . >/dev/null &&
      npx tsc --noEmit && npx vitest run 2>&1 | grep -E "Tests ") || { echo "STOP: frontend checks"; exit 1; }
  else
    echo "frontend untouched on both sides — checked already"
  fi
  # Formatting the tree is part of the checks above, so a rebase that left a
  # file unformatted gets its own commit rather than a dirty tree at push.
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    git commit -qam "style: format after rebase"
  fi
  git push -q --force-with-lease origin "$br" || exit 1
  # Wait for GitHub to agree that the head is what was just pushed, rather than
  # guessing how long that takes. `gh pr checks` reports the checks of the PR's
  # head commit, so once the two match, what it lists is this push's — which is
  # what the blind `sleep 20` here was reaching for, less certainly and more
  # slowly (it usually settles in a few seconds).
  head=$(git rev-parse HEAD)
  seen=
  for _ in $(seq 1 20); do
    seen=$(gh pr view "$n" --json headRefOid -q .headRefOid 2>/dev/null)
    [ "$seen" = "$head" ] && break
    sleep 3
  done
  [ "$seen" = "$head" ] || { echo "STOP: GitHub still does not see the push after 1 min"; exit 1; }
  # Wait for every check to report, and require all of them green, BEFORE
  # handing the PR to auto-merge. The other order merged #276 with
  # `backend-windows` red: a STOP here is only this script exiting, while
  # `--auto` is an instruction GitHub keeps and acts on, and GitHub waits for
  # the checks branch protection calls *required* — not for the ones this loop
  # reads. Arming it only once everything has reported means the two cannot
  # disagree about what green is.
  # Ten seconds rather than twenty: the wait is idle either way, and the run
  # spends it once per PR. At worst this asks 120 times per PR here and 60
  # below — nowhere near the 5,000 requests an hour the API allows.
  pending=
  for _ in $(seq 1 120); do
    # `|| true`, not `|| checks=`: gh exits 1 exactly when a check has failed,
    # and throwing the output away then would hide the one thing this looks for.
    checks=$(gh pr checks "$n" 2>/dev/null || true)
    bad=$(printf '%s\n' "$checks" | grep -v -E "\bpass\b|\bpending\b|skipping")
    if [ -n "$bad" ]; then echo "STOP: checks"; echo "$bad"; exit 1; fi
    pending=$(printf '%s\n' "$checks" | grep -c "\bpending\b")
    [ "$pending" = 0 ] && [ -n "$checks" ] && break
    sleep 10
  done
  [ "$pending" = 0 ] || { echo "STOP: checks still pending after 20 min"; exit 1; }
  gh pr merge "$n" --squash --auto >/dev/null 2>&1 ||
    { echo "STOP: could not enable auto-merge"; exit 1; }
  # The queue still has to wait: the next PR is rebased onto a main that
  # contains this one. Everything has reported by now, so this is short — and
  # if it does not merge, auto-merge is disarmed on the way out rather than
  # left to merge the branch later, unattended, after a STOP.
  state=
  for _ in $(seq 1 60); do
    state=$(gh pr view "$n" --json state -q .state)
    [ "$state" = MERGED ] && break
    sleep 5
  done
  if [ "$state" != MERGED ]; then
    gh pr merge "$n" --disable-auto >/dev/null 2>&1 || true
    echo "STOP: not merged 5 min after every check reported (auto-merge disarmed)"
    exit 1
  fi
  # The remote branch goes with the repository's delete-on-merge setting; the
  # local one is ours to clean up, and cannot be deleted while checked out.
  git switch -q main && git branch -qD "$br"
  echo "merged #$n"
done
cd "$here" && git switch -q main && git pull -q --ff-only && echo DONE
