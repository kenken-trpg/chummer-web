import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { renderNotice } from "@/lib/engine-notices";
import { useUiText } from "@/lib/i18n";

/**
 * What a .chum5 export would lose, shown before the file is written: the
 * player can export anyway (the loss is often acceptable — a house-ruled item
 * Chummer has no row for) or go back and change the character first.
 */
export function ExportReview({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { exportReview, confirmChum5, cancelChum5, tr } = ed;
  if (!exportReview) return null;
  return (
    <section
      className="warn export-review"
      role="alertdialog"
      aria-labelledby="export-review-title"
    >
      <p id="export-review-title">{ui("app.exportReview.title", { count: exportReview.length })}</p>
      <ul>
        {exportReview.map((d, i) => (
          <li key={`${d.key}-${i}`}>{renderNotice(d, ui, tr)}</li>
        ))}
      </ul>
      <button className="btn primary" onClick={() => void confirmChum5()}>
        {ui("app.exportReview.confirm")}
      </button>{" "}
      <button className="btn" onClick={cancelChum5}>
        {ui("app.exportReview.cancel")}
      </button>
    </section>
  );
}
