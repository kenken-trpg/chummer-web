#!/usr/bin/env bash
# Publish staged or committed changes; retain progress so a failed run can resume.
set -euo pipefail

usage() {
  cat <<'HELP'
Usage: scripts/publish.sh --title TITLE --body-file FILE
  --ci-workflow FILE --deploy-workflow FILE --deploy-input NAME
  --artifact-pattern REGEX [--message MESSAGE | --existing-commit | --resume]

--message MESSAGE   Commit already-staged changes (default mode).
--existing-commit   Publish the current commit; require a clean working tree.
--resume            Continue from the saved state; require a clean working tree.
--state-file FILE   Progress JSON (default: git's publish-state.json).
--log-dir DIR       Detailed logs (default: STATE_FILE.logs).
--preflight CMD     Run locally before pushing; environment includes PUBLISH_BASE
                    and PUBLISH_TITLE. Commands run from the repository root.
--verify-command CMD  Verify the public site after deployment: exit 0 = verified,
                      2 = verification incomplete, anything else = failure.
--deploy-run ID     Explicitly recover a dispatch whose run URL was not returned.

The default branch is the PR base. The artifact regex must have exactly one
capture group. Requires Bash, git, gh, Python 3 and authenticated GitHub access.
HELP
}
die() { echo "STOP: $*" >&2; exit 1; }
title= message= body_file= ci_workflow= deploy_workflow= deploy_input= artifact_pattern=
state_file= log_dir= preflight= verify_command= supplied_run=
mode=staged
while (($#)); do
  case "$1" in
    --existing-commit|--resume)
      [[ $mode == staged ]] || die 'choose only one publishing mode'
      mode=${1#--}; shift ;;
    --title|--message|--body-file|--ci-workflow|--deploy-workflow|--deploy-input|--artifact-pattern|--state-file|--log-dir|--preflight|--verify-command|--deploy-run)
      (($# >= 2)) || die "missing value for $1"
      case "$1" in
        --title) title=$2;; --message) message=$2;; --body-file) body_file=$2;;
        --ci-workflow) ci_workflow=$2;; --deploy-workflow) deploy_workflow=$2;;
        --deploy-input) deploy_input=$2;; --artifact-pattern) artifact_pattern=$2;;
        --state-file) state_file=$2;; --log-dir) log_dir=$2;; --preflight) preflight=$2;;
        --verify-command) verify_command=$2;; --deploy-run) supplied_run=$2;;
      esac
      shift 2 ;;
    -h|--help) usage; exit 0;;
    *) die "unknown option: $1" ;;
  esac
done
for value in "$title" "$body_file" "$ci_workflow" "$deploy_workflow" "$deploy_input" "$artifact_pattern"; do
  [[ -n $value ]] || { usage >&2; die 'missing required option'; }
done
[[ -f $body_file ]] || die "PR body file not found: $body_file"
body_file=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$body_file")
python3 -c 'import re,sys; assert re.compile(sys.argv[1]).groups == 1, "artifact regex must have one capture group"' "$artifact_pattern"
root=$(git rev-parse --show-toplevel)
# Resolve user paths before changing directories.
state_file=${state_file:-$(git rev-parse --git-path publish-state.json)}
state_file=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$state_file")
log_dir=${log_dir:-$state_file.logs}
log_dir=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$log_dir")
cd "$root"
mkdir -p "$(dirname "$state_file")" "$log_dir"
mkdir "$state_file.lock" 2>/dev/null || die "another publisher holds $state_file.lock (remove only if no publisher is running)"
trap 'rmdir "$state_file.lock"; echo "State: $state_file"; echo "Logs: $log_dir"' EXIT
logged() {
  local label=$1; shift
  echo "$label ..."
  if "$@" >"$log_dir/$label.log" 2>&1; then return 0; else
    local result=$?
    tail -n 40 "$log_dir/$label.log" >&2
    return "$result"
  fi
}
logged auth gh auth status
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
base=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
branch=$(git branch --show-current)
[[ -n $branch && $branch != "$base" ]] || die "switch to a feature branch (base: $base)"
config=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "$repo" "$base" "$branch" "$ci_workflow" "$deploy_workflow" "$deploy_input" "$artifact_pattern" "$preflight" "$verify_command")
pr= merge_sha= ci_run= artifact= deploy_run= dispatch_pending=
get_state() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' "$state_file" "$1"; }
save_state() {
  python3 - "$state_file" "$config" "$head_sha" "$pr" "$merge_sha" "$ci_run" "$artifact" "$deploy_run" "$dispatch_pending" <<'PY'
import json, os, sys
path = sys.argv[1]
keys = ('config', 'head_sha', 'pr', 'merge_sha', 'ci_run', 'artifact', 'deploy_run', 'dispatch_pending')
with open(path + '.tmp', 'w') as out:
    json.dump(dict(zip(keys, sys.argv[2:])), out, indent=2)
    out.write('\n')
os.replace(path + '.tmp', path)
PY
}
if [[ $mode == staged ]]; then
  [[ ! -e $state_file ]] || die 'saved progress exists; use --resume or another --state-file'
  [[ -n $message ]] || die '--message is required for staged changes'
  [[ -n $(git diff --cached --name-only) ]] || die 'stage the changes to commit first'
  [[ -z $(git diff --name-only) ]] || die 'unstaged tracked changes exist'
  git diff --cached --check
  logged commit git commit -m "$message"
fi
[[ -z $(git status --porcelain) ]] || die 'working tree has uncommitted changes'
head_sha=$(git rev-parse HEAD)
if [[ $mode == resume ]]; then
  [[ -f $state_file ]] || die 'no saved state; use --existing-commit first'
  [[ $(get_state config) == "$config" ]] || die 'saved repository, branch or workflow options differ'
  pr=$(get_state pr); merge_sha=$(get_state merge_sha)
  ci_run=$(get_state ci_run); artifact=$(get_state artifact)
  deploy_run=$(get_state deploy_run); dispatch_pending=$(get_state dispatch_pending)
  if [[ $(get_state head_sha) != "$head_sha" ]]; then
    [[ -z $merge_sha ]] || die 'HEAD changed after merging; start a new publication'
    [[ -z $pr || $(gh pr view "$pr" --repo "$repo" --json state --jq .state) == OPEN ]] || die 'HEAD changed after PR closed'
    ci_run= artifact= deploy_run= dispatch_pending=
  fi
else
  [[ ! -e $state_file ]] || die 'saved progress exists; use --resume or another --state-file'
fi
save_state
export PUBLISH_BASE="origin/$base" PUBLISH_TITLE="$title"
if [[ -z $merge_sha ]]; then
  logged fetch git fetch origin "$base"
  if [[ -n $preflight ]]; then logged preflight bash -c "$preflight"; fi
  logged push git push -u origin "$branch"
  if [[ -z $pr ]]; then
    pr=$(gh pr list --repo "$repo" --head "$branch" --base "$base" --state all --limit 30 --json url,headRefOid,state --jq ".[] | select(.headRefOid == \"$head_sha\" and .state != \"CLOSED\") | .url" | head -n 1)
    if [[ -z $pr ]]; then
      pr=$(gh pr create --repo "$repo" --base "$base" --head "$branch" --title "$title" --body-file "$body_file")
    fi
    save_state
  fi
  echo "PR: $pr"
  [[ $(gh pr view "$pr" --repo "$repo" --json headRefOid --jq .headRefOid) == "$head_sha" ]] || die 'PR head differs from local HEAD; retry after GitHub updates'
  if [[ $(gh pr view "$pr" --repo "$repo" --json state --jq .state) != MERGED ]]; then
    registered=false
    for ((i=0; i<60; i++)); do
      count=$(gh api "repos/$repo/commits/$head_sha/check-runs" --jq .total_count)
      if ((count > 0)); then registered=true; break; fi
      sleep 3
    done
    [[ $registered == true ]] || die 'checks for the current commit were not registered'
    logged pr-checks gh pr checks "$pr" --repo "$repo" --watch --interval 10 --fail-fast
    logged merge gh pr merge "$pr" --repo "$repo" --squash --match-head-commit "$head_sha"
  fi
  merge_sha=$(gh pr view "$pr" --repo "$repo" --json mergeCommit --jq '.mergeCommit.oid // empty')
  [[ -n $merge_sha ]] || die 'could not identify merge commit'
  save_state
fi
if [[ -z $ci_run ]]; then
  for ((i=0; i<60; i++)); do
    ci_run=$(gh run list --repo "$repo" --workflow "$ci_workflow" --event push --branch "$base" --commit "$merge_sha" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
    [[ -z $ci_run ]] || break
    sleep 3
  done
  [[ -n $ci_run ]] || die 'CI run for the merge commit was not found'
  save_state
fi
logged ci gh run watch "$ci_run" --repo "$repo" --exit-status --interval 10
if [[ -z $artifact ]]; then
  logged ci-artifact gh run view "$ci_run" --repo "$repo" --log
  artifact=$(python3 - "$artifact_pattern" "$log_dir/ci-artifact.log" <<'PY'
import re, sys
pattern = re.compile(sys.argv[1])
with open(sys.argv[2]) as log:
    hits = {m.group(1) for line in log for m in pattern.finditer(line)}
if len(hits) != 1:
    sys.exit('STOP: expected exactly one immutable artifact reference')
print(hits.pop())
PY
)
  save_state
fi
validate_deploy_run() {
# Validate even explicitly supplied run IDs, rather than watching an unrelated run.
gh api "repos/$repo/actions/runs/$1" >"$log_dir/deploy-metadata.json"
python3 - "$log_dir/deploy-metadata.json" "$merge_sha" "$deploy_workflow" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    run = json.load(f)
if (run['head_sha'] != sys.argv[2] or run['event'] != 'workflow_dispatch'
        or run['path'] != '.github/workflows/' + sys.argv[3]):
    sys.exit('STOP: deployment run does not match the merge commit and workflow')
PY
}
if [[ -n $supplied_run ]]; then
  [[ $supplied_run =~ ^[0-9]+$ ]] || die '--deploy-run must be numeric'
  [[ -z $deploy_run || $deploy_run == "$supplied_run" ]] || die 'a different deployment is already saved'
  validate_deploy_run "$supplied_run"
  deploy_run=$supplied_run
  save_state
fi
if [[ -z $deploy_run ]]; then
  [[ -z $dispatch_pending ]] || die 'dispatch may already exist; recover with --resume --deploy-run ID; do not blindly dispatch again'
  current_base=$(gh api "repos/$repo/git/ref/heads/$base" --jq .object.sha)
  [[ $current_base == "$merge_sha" ]] || die "$base advanced after CI; confirm the intended artifact before deploying"
  dispatch_pending=yes
  save_state
  logged dispatch gh workflow run "$deploy_workflow" --repo "$repo" --ref "$base" -f "$deploy_input=$artifact"
  deploy_run=$(python3 -c 'import re,sys; m=re.search(r"https://github\.com/" + re.escape(sys.argv[1]) + r"/actions/runs/(\d+)", open(sys.argv[2]).read()); print(m.group(1) if m else "")' "$repo" "$log_dir/dispatch.log")
  [[ -n $deploy_run ]] || die 'dispatch returned no run URL; recover with --resume --deploy-run ID'
  save_state
fi
validate_deploy_run "$deploy_run"
logged deploy gh run watch "$deploy_run" --repo "$repo" --exit-status --interval 10
gh run view "$deploy_run" --repo "$repo" --json jobs --jq '.jobs' | python3 -c 'import json,sys; jobs=json.load(sys.stdin); sys.exit(0 if jobs and all(j["conclusion"] == "success" for j in jobs) else "STOP: deployment has skipped or failed jobs")'
logged deploy-details gh run view "$deploy_run" --repo "$repo" --log
verification='not configured'
verify_result=0
if [[ -n $verify_command ]]; then
  if logged public-check bash -c "$verify_command"; then verification=verified; else
    verify_result=$?
    if ((verify_result == 2)); then verification=incomplete; verify_result=0; else verification=failed; fi
  fi
fi
printf 'PR: %s\nMerge: %s\nArtifact: %s\nDeployment: https://github.com/%s/actions/runs/%s\nDeployment status: succeeded\nPublic verification: %s\n' "$pr" "$merge_sha" "$artifact" "$repo" "$deploy_run" "$verification"
exit "$verify_result"
