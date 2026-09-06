import { useUiText } from "@/lib/i18n";

/** Where the code lives and who wrote it. The sheet has carried a footer all
 *  along; the editor had none, so the app was anonymous on every screen but
 *  the last one. */
export const REPO_URL = "https://github.com/kenken-trpg/chummer-web";
export const AUTHOR = "kenken-trpg";

export function AppFooter() {
  const { ui } = useUiText();
  return (
    <footer className="app-footer no-print">
      <span>{ui("app.footer.author", { author: AUTHOR })}</span>
      <span aria-hidden="true">・</span>
      <a
        href={REPO_URL}
        target="_blank"
        rel="noopener noreferrer"
        title={ui("app.footer.repoHint")}
      >
        {ui("app.footer.repo")}
      </a>
      <span aria-hidden="true">・</span>
      <span>{ui("app.footer.license")}</span>
    </footer>
  );
}
