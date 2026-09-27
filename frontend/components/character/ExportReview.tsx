import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";
import { ReviewPanel } from "./ReviewPanel";

/**
 * What an export would lose, shown before the file is written: the player can
 * export anyway (the loss is often acceptable — a house-ruled item Chummer has
 * no row for, or a program inside a commlink the character sheet has no cell
 * for) or go back and change the character first.
 *
 * Shared by both formats that have to be read back out of a file: which one was
 * asked for is the editor's to remember, so confirming writes the right one.
 *
 * Equipment rows still waiting to be confirmed are counted here as well. Those
 * rows are kept in this browser only — they go to neither the server nor a
 * share link — so an export written before they are settled simply does not
 * contain them, and until now it said nothing about it.
 */
export function ExportReview({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { exportReview, exportReviewFormat, pendingGear, confirmExport, cancelExport, tr } = ed;
  if (!exportReview) return null;
  const unsettled = pendingGear?.length ?? 0;
  return (
    <ReviewPanel
      id="export-review-title"
      title={
        exportReview.length
          ? ui("app.exportReview.title", {
              count: exportReview.length,
              format: `.${exportReviewFormat ?? "chum5"}`,
            })
          : ui("app.exportReview.unsettled", { count: unsettled })
      }
      notices={exportReview}
      tr={tr}
    >
      {exportReview.length && unsettled ? (
        <p>{ui("app.exportReview.unsettled", { count: unsettled })}</p>
      ) : null}
      <button className="btn primary" onClick={() => void confirmExport()}>
        {ui("app.exportReview.confirm")}
      </button>{" "}
      <button className="btn" onClick={cancelExport}>
        {ui("app.exportReview.cancel")}
      </button>
    </ReviewPanel>
  );
}
