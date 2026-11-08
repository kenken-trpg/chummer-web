import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";
import { HelpTip } from "@/components/help/HelpTip";

export function BulkImportReview({ ed }: { ed: CharacterEditor }) {
  const { ui, locale } = useUiText();
  const backup = ed.bulkImport;
  if (!backup) return null;
  const selected = new Set(ed.bulkSelection);
  return (
    <section className="notice" aria-labelledby="bulk-import-title" aria-busy={ed.bulkBusy}>
      <p id="bulk-import-title">{ui("app.bulk.review")}</p>
      <p>{ui("app.bulk.created", { date: new Date(backup.createdAt).toLocaleString(locale) })}</p>
      <p>
        <HelpTip
          label={ui("help.open", { label: ui("app.bulk.review") })}
          lines={[{ label: ui("help.bulk.twice") }, { label: ui("help.bulk.recompute") }]}
        >
          {ui("app.bulk.copies")}
        </HelpTip>
      </p>
      <fieldset disabled={ed.bulkBusy}>
        <legend>{ui("app.bulk.choose")}</legend>
        <button
          className="btn"
          onClick={() => ed.selectBulkImport(backup.characters.map((_, index) => index))}
        >
          {ui("app.bulk.all")}
        </button>
        <button className="btn" onClick={() => ed.selectBulkImport([])}>
          {ui("app.bulk.none")}
        </button>
        <ul>
          {backup.characters.map((character, index) => (
            <li key={index}>
              <label>
                <input
                  type="checkbox"
                  checked={selected.has(index)}
                  onChange={(e) => {
                    const next = new Set(selected);
                    if (e.target.checked) next.add(index);
                    else next.delete(index);
                    ed.selectBulkImport([...next]);
                  }}
                />{" "}
                {character.name || ui("toolbar.unnamed")} ・ {ed.tr(character.metatype)} ・{" "}
                {ui(character.career ? "app.roster.career" : "app.roster.creation")}
              </label>
            </li>
          ))}
        </ul>
      </fieldset>
      <p role="status">
        {ui(ed.bulkBusy ? "app.bulk.importing" : "app.bulk.selected", { count: selected.size })}
      </p>
      <button
        className="btn primary"
        disabled={ed.bulkBusy || !selected.size}
        onClick={() => void ed.confirmBulkImport()}
      >
        {ui("app.bulk.confirm")}
      </button>
      <button className="btn" disabled={ed.bulkBusy} onClick={ed.cancelBulkImport}>
        {ui("app.bulk.cancel")}
      </button>
    </section>
  );
}
