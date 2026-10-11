# Agent instructions

## Language

- Always respond to the user in Japanese.

## Frontend development: Next.js

- When working in `frontend/`, do not assume that the installed Next.js version matches your training data. This version has breaking changes; APIs, conventions, and file structure may differ.
- Before writing frontend code, read the relevant guide in `frontend/node_modules/next/dist/docs/`. Resolve the Next.js package from `frontend/`, since it may not be visible from the repository root in a monorepo.
- Heed deprecation notices in the Next.js documentation.

## Next.js-generated agent instructions

- The Next.js instruction block in `frontend/AGENTS.md` is written and re-added by `next dev`. Verify this behavior in `frontend/node_modules/next/dist/server/lib/generate-agent-files.js`.
- `frontend/AGENTS.md` and `frontend/CLAUDE.md` are untracked: `.gitignore` lists them, since #19 stopped tracking them. They never show up in a diff, so leave them where `next dev` put them — there is nothing to commit and nothing to delete.
