import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { renderNotice } from "@/lib/engine-notices";
import { useUiText } from "@/lib/i18n";

/**
 * What an export would lose, shown before the file is written: the player can
 * export anyway (the loss is often acceptable — a house-ruled item Chummer has
 * no row for, or a program inside a commlink the character sheet has no cell
 * for) or go back and change the character first.
 *
 * Shared by both formats that have to be read back out of a file: which one was
 * asked for is the editor's to remember, so confirming writes the right one.
 */
export function ExportReview({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { exportReview, exportReviewFormat, confirmExport, cancelExport, tr } = ed;
  if (!exportReview) return null;
  return (
    <section
      className="warn export-review"
      role="alertdialog"
      aria-labelledby="export-review-title"
    >
      <p id="export-review-title">
        {ui("app.exportReview.title", {
          count: exportReview.length,
          format: `.${exportReviewFormat ?? "chum5"}`,
        })}
      </p>
      <ul>
        {exportReview.map((d, i) => (
          <li key={`${d.key}-${i}`}>{renderNotice(d, ui, tr)}</li>
        ))}
      </ul>
      <button className="btn primary" onClick={() => void confirmExport()}>
        {ui("app.exportReview.confirm")}
      </button>{" "}
      <button className="btn" onClick={cancelExport}>
        {ui("app.exportReview.cancel")}
      </button>
    </section>
  );
}
