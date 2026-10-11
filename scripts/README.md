# Publishing

`publish.sh` pushes a feature branch, creates or reuses its PR, waits for checks,
merges it, waits for CI on that exact merge commit, and deploys the immutable
artifact extracted from that CI's logs. It changes the live service.
Requires Bash, git, authenticated GitHub CLI (`gh`) and Python 3.

For this repository, use the thin wrapper with Chummer's workflow names, image
pattern, changelog preflight and public endpoint verification:

```sh
bash scripts/publish-chummer.sh --existing-commit \
  --title 'Describe the resulting change' --body-file /tmp/pr-description.md
```

The default mode commits **already-staged** changes and requires `--message`.
`--existing-commit` starts from HEAD and requires a clean working tree. Both
modes refuse to overwrite existing progress. PR descriptions should be outside
the working tree. The preflight runs after any commit, before pushing; it checks
the changelog fragment against the freshly fetched base branch.

## Resuming

Progress defaults to `git rev-parse --git-path publish-state.json`, outside the
tracked files and separate for each worktree. Detailed logs go beside it in
`publish-state.json.logs/`. Use `--state-file FILE` and `--log-dir DIR` to choose
other locations. A lock directory prevents simultaneous use of the same state.
After a crash, remove the lock only after confirming no publisher is running.

After a failure, repeat the same command with `--resume` in place of
`--existing-commit` (or in place of `--message MESSAGE` for staged mode):

```sh
bash scripts/publish-chummer.sh --resume \
  --title 'Describe the resulting change' --body-file /tmp/pr-description.md
```

If PR checks failed, fix and commit the change before resuming. A changed HEAD
is accepted only while the saved PR is still open and unmerged. Checks must
exist for the new commit; the merge requires that exact PR head. A merged PR is
reused on restart, including if the process stopped before saving the merge.
After merging, HEAD and the saved repository/workflow configuration must match.

A resume reuses the CI and deployment run IDs already saved. It does not dispatch
another deployment, including after a public verification failure. To retry a
failed workflow, rerun that run in GitHub, then resume. If dispatch succeeded but
its URL was lost (or `gh` did not return one), the script stops rather than guess
which concurrent run belongs to it. Inspect GitHub's run and its image input,
then recover with `--resume --deploy-run ID`. The run's workflow, event and commit
are checked. The saved state belongs to one publication; use another state file
for the next publication or archive the old state after completion.

## Generic configuration

Projects with different workflows can call the common script directly:

```sh
bash scripts/publish.sh --existing-commit \
  --title 'Improve reporting' --body-file /tmp/pr-description.md \
  --ci-workflow ci.yml --deploy-workflow deploy.yml --deploy-input image \
  --artifact-pattern 'published image: (registry\.example/[^ ]+@sha256:[0-9a-f]{64})'
```

The Python regex must have exactly one capture group and find exactly one unique
artifact reference. The script stops if the base branch advances before dispatch,
checks fail, or deployment jobs fail or are skipped. The deployment workflow
must support `workflow_dispatch`; a recent `gh` that returns the dispatched run
URL avoids manual recovery. It never selects the latest unrelated deployment.

Optional `--preflight COMMAND` and `--verify-command COMMAND` run trusted shell
commands from the repository root. Preflight receives `PUBLISH_BASE` (e.g.
`origin/main`) and `PUBLISH_TITLE`. Public verification exits 0 for success, 2 for
incomplete verification, or another code for failure. Chummer's
`verify-public.sh` checks HTTP status and content at `/api/ready` and `/`; a
Cloudflare challenge is incomplete. A real HTTP/content error fails the command
even though deployment already succeeded.

Normal output shows stages and a final PR/merge/artifact/deployment/public-status
report. Full watch output and deployment logs (including serving revision and
traffic information) stay in the log directory; failed stages print their last
40 log lines. Public verification and deployment success are reported separately.

Offline regression tests (no GitHub access or deployment):

```sh
python3 -m unittest discover -s scripts/tests -p 'test_publish.py'
```
