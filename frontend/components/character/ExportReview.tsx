import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";
import { ReviewPanel } from "./ReviewPanel";

/**
 * What an export would lose, shown before the file is written: the player can
 * export anyway (the loss is often acceptable — a house-ruled item Chummer has
 * no row for, or a program inside a commlink the character sheet has no cell
 * for) or go back and change the character first.
 *
 * Shared by the checked export formats: which one was
 * asked for is the editor's to remember, so confirming writes the right one.
 *
 * Equipment rows still waiting to be confirmed are counted here as well. Those
 * rows are kept in this browser only — they go to neither the server nor a
 * share link — so an export written before they are settled simply does not
 * contain them, and until now it said nothing about it.
 */
/** The notices that say what Chummer's settings take from the file. */
const CHUMMER_SETTINGS = new Set([
  "engine.export.chum5SettingsAs",
  "engine.export.chum5QualityCap",
  "engine.export.chum5AvailMax",
  "engine.export.chum5NuyenCap",
  "engine.export.chum5PriorityTable",
  "engine.export.chum5Books",
  "engine.export.chum5BooksAll",
  "engine.export.chum5Nuyen",
]);

export function ExportReview({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const {
    exportReview,
    exportReviewFormat,
    pendingGear,
    confirmExport,
    downloadChum5WithSettings,
    cancelExport,
    tr,
  } = ed;
  if (!exportReview) return null;
  const unsettled = pendingGear?.length ?? 0;
  // what Chummer's own settings would take, which a settings file of the
  // character's own keeps (`chummer_settings_losses` on the server)
  const settingsLost =
    exportReviewFormat === "chum5" && exportReview.some((n) => CHUMMER_SETTINGS.has(n.key));
  return (
    <ReviewPanel
      id="export-review-title"
      title={
        exportReview.length
          ? ui(
              exportReviewFormat === "fvtt"
                ? "app.exportReview.fvttTitle"
                : "app.exportReview.title",
              {
                count: exportReview.length,
                format:
                  exportReviewFormat === "fvtt"
                    ? "Foundry VTT JSON"
                    : `.${exportReviewFormat ?? "chum5"}`,
              },
            )
          : ui("app.exportReview.unsettled", { count: unsettled })
      }
      notices={exportReview}
      tr={tr}
    >
      {exportReview.length && unsettled ? (
        <p>{ui("app.exportReview.unsettled", { count: unsettled })}</p>
      ) : null}
      {settingsLost ? <p>{ui("app.exportReview.withSettingsHint")}</p> : null}
      {settingsLost ? (
        <>
          <button className="btn primary" onClick={() => void downloadChum5WithSettings()}>
            {ui("app.exportReview.withSettings")}
          </button>{" "}
        </>
      ) : null}
      <button className={settingsLost ? "btn" : "btn primary"} onClick={() => void confirmExport()}>
        {ui("app.exportReview.confirm")}
      </button>{" "}
      <button className="btn" onClick={cancelExport}>
        {ui("app.exportReview.cancel")}
      </button>
    </ReviewPanel>
  );
}
