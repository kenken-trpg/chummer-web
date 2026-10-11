# changelog.d

One file per PR, instead of an edit to `CHANGELOG.md`. Two PRs never touch the
same file, so they never conflict here.

- Name: `<anything-unique>.<type>.md` — the branch name works, e.g.
  `export-check-panel.changed.md`.
- Type: `added`, `changed`, `deprecated`, `removed`, `fixed` or `security`
  (the Keep a Changelog headings).
- Content: the entry exactly as it should appear under that heading — usually
  one `- **…**` bullet, with continuation lines indented two spaces.
  Several bullets in one file are fine.

`collect` pastes a fragment in verbatim, so a fragment that is not a list item
lands in the section as a paragraph between the bullets. The `changelog` job
checks that much — a `- ` bullet, continuation lines indented two spaces — and
leaves the bold lead-in to you.

CI (`changelog` job) fails a PR that changes `backend/`, `frontend/` or the
Docker files without adding a fragment. Put `[skip changelog]` in the PR title
for a change nobody would notice.

Dependabot PRs that change only dependency manifests or the Dockerfile need no
fragment; their PRs and release history record the updates. Bot PRs that change
application code still need a fragment.

At release, `make changelog` folds every fragment into `## [Unreleased]` and
deletes them; `make release-check` fails while any are left. See
CONTRIBUTING.md › Releasing.
