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

CI (`changelog` job) fails a PR that changes `backend/`, `frontend/` or the
Docker files without adding a fragment. Put `[skip changelog]` in the PR title
for a change nobody would notice.

At release, `make changelog` folds every fragment into `## [Unreleased]` and
deletes them; `make release-check` fails while any are left. See
CONTRIBUTING.md › Releasing.
