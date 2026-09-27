import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";
import { ReviewPanel } from "./ReviewPanel";

/**
 * What an import could not bring over, listed once the character is open.
 *
 * This used to arrive as the red error box holding all of it on one line, which
 * was wrong twice: the import did not fail — the character is open and usable —
 * and fifteen notices joined by slashes is not something anyone reads. It is the
 * same report the export asks for in advance, so it is shown the same way.
 *
 * Dismissed by the player rather than by a timer: the point is to be read, and
 * what is in it (a quality the book has no row for, an item the sheet's free
 * text could not be matched to) is often something to go and fix by hand.
 */
export function ImportReport({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { importReport, dismissImportReport, tr } = ed;
  if (!importReport) return null;
  return (
    <ReviewPanel
      id="import-report-title"
      title={ui("app.importReport.title", { count: importReport.length })}
      notices={importReport}
      tr={tr}
    >
      <button className="btn" onClick={dismissImportReport}>
        {ui("app.importReport.dismiss")}
      </button>
    </ReviewPanel>
  );
}
