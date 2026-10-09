#!/usr/bin/env bash
# Commit staged changes, open and merge a PR, then deploy an immutable CI artifact.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/publish.sh --title TITLE --message MESSAGE --body-file FILE \
    --ci-workflow FILE --deploy-workflow FILE --deploy-input NAME \
    --artifact-pattern REGEX

Required options:
  --title TITLE                 Pull request title
  --message MESSAGE             Commit message
  --body-file FILE              Pull request description
  --ci-workflow FILE            CI workflow triggered by a push to the base branch
  --deploy-workflow FILE        Workflow accepting workflow_dispatch
  --deploy-input NAME           Dispatch input receiving the artifact reference
  --artifact-pattern REGEX      Python regex with one capture group matching
                                the immutable artifact reference in CI logs

Only already-staged changes are committed. The current branch is the PR head;
the repository default branch is the base. Requires git, gh, Python 3, and
authenticated GitHub CLI access.
EOF
}

die() { echo "STOP: $*" >&2; exit 1; }
title= message= body_file= ci_workflow= deploy_workflow= deploy_input= artifact_pattern=
while (($#)); do
  case "$1" in
    --title|--message|--body-file|--ci-workflow|--deploy-workflow|--deploy-input|--artifact-pattern)
      (($# >= 2)) || { usage >&2; exit 2; }
      key=${1#--}; value=$2; shift 2
      case "$key" in
        title) title=$value;; message) message=$value;; body-file) body_file=$value;;
        ci-workflow) ci_workflow=$value;; deploy-workflow) deploy_workflow=$value;;
        deploy-input) deploy_input=$value;; artifact-pattern) artifact_pattern=$value;;
      esac ;;
    -h|--help) usage; exit 0;;
    *) usage >&2; die "unknown option: $1";;
  esac
done
for pair in "title:$title" "message:$message" "body file:$body_file" \
  "CI workflow:$ci_workflow" "deploy workflow:$deploy_workflow" \
  "deploy input:$deploy_input" "artifact pattern:$artifact_pattern"; do
  [[ ${pair#*:} ]] || die "missing required ${pair%%:*}"
done
[[ -f $body_file ]] || die "PR body file not found: $body_file"

gh auth status >/dev/null
git rev-parse --show-toplevel >/dev/null 2>&1 || die 'run inside a git repository'
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
base=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
branch=$(git branch --show-current)
[[ -n $branch && $branch != "$base" ]] || die "switch to a feature branch (base: $base)"
[[ -n $(git diff --cached --name-only) ]] || die 'stage the changes to commit first'
[[ -z $(git diff --name-only) ]] || die 'unstaged tracked changes exist; stage or restore them first'
git diff --cached --check
git commit -m "$message"
head_sha=$(git rev-parse HEAD)
git push -u origin "$branch"

pr=$(gh pr list --repo "$repo" --head "$branch" --base "$base" --state open --json url --jq '.[0].url // empty')
if [[ -z $pr ]]; then
  pr=$(gh pr create --repo "$repo" --base "$base" --head "$branch" --title "$title" --body-file "$body_file")
fi
echo "PR: $pr"
pr_state=$(gh pr view "$pr" --repo "$repo" --json state --jq .state)
if [[ $pr_state != MERGED ]]; then
  ready=false
  for ((i=0; i<60; i++)); do
    count=$(gh pr view "$pr" --repo "$repo" --json statusCheckRollup --jq '.statusCheckRollup | length')
    if ((count > 0)); then ready=true; break; fi
    sleep 3
  done
  [[ $ready == true ]] || die 'PR checks were not registered'
  gh pr checks "$pr" --repo "$repo" --watch --interval 10 --fail-fast
  gh pr merge "$pr" --repo "$repo" --squash --match-head-commit "$head_sha"
fi
merge_sha=$(gh pr view "$pr" --repo "$repo" --json mergeCommit --jq '.mergeCommit.oid')
[[ $merge_sha && $merge_sha != null ]] || die 'could not identify merge commit'

ci_run=
for ((i=0; i<60; i++)); do
  ci_run=$(gh run list --repo "$repo" --workflow "$ci_workflow" --event push --branch "$base" --commit "$merge_sha" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  [[ -z $ci_run ]] || break
  sleep 3
done
[[ $ci_run ]] || die 'CI run for the merge commit was not found'
gh run watch "$ci_run" --repo "$repo" --exit-status --interval 10

artifact=$(gh run view "$ci_run" --repo "$repo" --log | python3 -c \
  'import re,sys; p=re.compile(sys.argv[1]); hits=[m.group(1) for line in sys.stdin for m in [p.search(line)] if m]; print(hits[-1] if hits else "")' \
  "$artifact_pattern")
[[ $artifact ]] || die 'could not extract immutable artifact reference from CI logs'
current_base=$(gh api "repos/$repo/git/ref/heads/$base" --jq .object.sha)
[[ $current_base == "$merge_sha" ]] || die "$base advanced after CI; confirm the artifact before deploying"

prior_run=$(gh run list --repo "$repo" --workflow "$deploy_workflow" --event workflow_dispatch --branch "$base" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
gh workflow run "$deploy_workflow" --repo "$repo" --ref "$base" -f "$deploy_input=$artifact"
deploy_run=
for ((i=0; i<60; i++)); do
  candidate=$(gh run list --repo "$repo" --workflow "$deploy_workflow" --event workflow_dispatch --branch "$base" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  if [[ $candidate && $candidate != "$prior_run" ]]; then deploy_run=$candidate; break; fi
  sleep 3
done
[[ $deploy_run ]] || die 'deployment run was not found'
gh run watch "$deploy_run" --repo "$repo" --exit-status --interval 10
gh run view "$deploy_run" --repo "$repo" --json jobs --jq '.jobs' | python3 -c \
  'import json,sys; jobs=json.load(sys.stdin); sys.exit(0 if jobs and all(j["conclusion"] == "success" for j in jobs) else "STOP: deployment has skipped or failed jobs")'
echo "Complete: $pr"
echo "Artifact: $artifact"
echo "Deployment: https://github.com/$repo/actions/runs/$deploy_run"
