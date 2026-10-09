# Generic publish command

`scripts/publish.sh` commits staged changes, pushes the current branch, creates
(or reuses) a pull request, waits for checks, merges it, waits for CI on the
default branch, extracts an immutable artifact reference from CI logs, and
dispatches a deployment workflow with that reference.

Requirements: Bash, Git, GitHub CLI (`gh`) authenticated for the repository,
and Python 3. Configure the workflow names, deployment input, and artifact log
pattern for the target repository. The artifact pattern must contain exactly
the desired reference in capture group 1.

Example:

```sh
scripts/publish.sh \
  --title 'Release: improve reporting' \
  --message 'Improve reporting' \
  --body-file /path/to/pull-request.md \
  --ci-workflow ci.yml \
  --deploy-workflow deploy.yml \
  --deploy-input image \
  --artifact-pattern 'published image: (ghcr\\.io/[^[:space:]]+@sha256:[0-9a-f]{64})'
```

Stage only the changes intended for the commit before running the command.
The command stops if tracked unstaged changes remain, checks fail, the base
branch advances after CI, or deployment jobs fail or are skipped. Review the
repository's workflow behavior and required deployment inputs before using it:
the final workflow dispatch may change a live service.
