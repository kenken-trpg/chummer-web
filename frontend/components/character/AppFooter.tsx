import { releaseUrl } from "@/lib/app-version";
import { useUiText } from "@/lib/i18n";

/** Where the code lives and who wrote it. The sheet has carried a footer all
 *  along; the editor had none, so the app was anonymous on every screen but
 *  the last one. */
export const REPO_URL = "https://github.com/kenken-trpg/chummer-web";
export const AUTHOR = "kenken-trpg";
/** `public/manual/index.html`, reached through the rewrite in `next.config.ts`. */
export const MANUAL_URL = "/manual";

/** Inlined at build time from `backend/pyproject.toml` (`next.config.ts`);
 *  empty when the build had no such file. */
export const APP_VERSION = process.env.APP_VERSION ?? "";

export function AppFooter({ version = APP_VERSION }: { version?: string } = {}) {
  const { ui } = useUiText();
  return (
    <footer className="app-footer no-print">
      <span>{ui("app.footer.author", { author: AUTHOR })}</span>
      <span aria-hidden="true">・</span>
      <a href={MANUAL_URL} target="_blank" rel="noopener noreferrer">
        {ui("app.footer.manual")}
      </a>
      <span aria-hidden="true">・</span>
      <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
        {ui("app.footer.repo")}
      </a>
      <span aria-hidden="true">・</span>
      <span>{ui("app.footer.license")}</span>
      {version && (
        <>
          <span aria-hidden="true">・</span>
          <a href={releaseUrl(REPO_URL, version)} target="_blank" rel="noopener noreferrer">
            {ui("app.footer.version", { version })}
          </a>
        </>
      )}
    </footer>
  );
}
