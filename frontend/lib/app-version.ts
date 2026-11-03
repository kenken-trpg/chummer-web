/** The version the footer shows, taken from `backend/pyproject.toml` at build
 *  time — the same `version = "…"` that `/api/version` reports and that
 *  `make release-check` holds to the tag. `next.config.ts` reads the file and
 *  inlines the result, so the page asks the server nothing to show it.
 *
 *  The frontend and the backend ship in one image built from one commit
 *  (`Dockerfile`), so the two cannot disagree in a deployment. */

/** The `[project]` table's `version`, or `undefined` when there is none. */
export function projectVersion(pyproject: string): string | undefined {
  let inProject = false;
  for (const raw of pyproject.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("[")) {
      inProject = line === "[project]";
      continue;
    }
    if (!inProject || !line.startsWith("version")) continue;
    const eq = line.indexOf("=");
    if (eq < 0 || line.slice(0, eq).trim() !== "version") continue;
    const value = line.slice(eq + 1).trim();
    if (value.length > 2 && value.startsWith('"') && value.endsWith('"')) {
      return value.slice(1, -1);
    }
  }
  return undefined;
}

/** The release page for a version — CI publishes one for every `v*` tag. */
export function releaseUrl(repo: string, version: string): string {
  return `${repo}/releases/tag/v${version}`;
}
