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
  const { importReport, importSummary, dismissImportReport, tr } = ed;
  if (!importReport && !importSummary) return null;
  const names = new Map<string, string>();
  const catalogRows = [
    ...Object.values(ed.catalog ?? {}).flatMap((value) => (Array.isArray(value) ? value : [])),
    ...(ed.catalog?.cyberware?.items ?? []),
    ...(ed.catalog?.bioware?.items ?? []),
  ];
  for (const row of catalogRows) {
    if (
      row &&
      typeof row === "object" &&
      "id" in row &&
      "name" in row &&
      typeof row.id === "string" &&
      typeof row.name === "string"
    )
      names.set(row.id, row.name);
  }
  function itemName(item: {
    ware_id?: string;
    gear_id?: string;
    spell_id?: string;
    armor_id?: string;
    weapon_id?: string;
  }) {
    const id =
      item.ware_id ?? item.gear_id ?? item.spell_id ?? item.armor_id ?? item.weapon_id ?? "";
    return tr(names.get(id) ?? id);
  }
  return (
    <ReviewPanel
      id="import-report-title"
      title={
        importSummary
          ? ui("app.importReport.success", { name: importSummary.name })
          : ui("app.importReport.title", { count: importReport?.length ?? 0 })
      }
      notices={importReport ?? []}
      tr={tr}
    >
      {importSummary ? (
        <p>
          {ui("app.importReport.summary", {
            skills: Object.keys(importSummary.skills).length,
            qualities: importSummary.quality_ids.length,
            contacts: importSummary.contacts?.length ?? 0,
          })}
        </p>
      ) : null}
      {importSummary ? (
        <ul>
          {(
            [
              ["tab.cyber", importSummary.cyberware],
              ["tab.bio", importSummary.bioware],
              ["tab.spells", importSummary.spells],
              [
                "tab.gear",
                [
                  ...(importSummary.gear ?? []),
                  ...(importSummary.weapons ?? []),
                  ...(importSummary.armor ?? []),
                  ...(importSummary.commlinks ?? []),
                  ...(importSummary.cyberdecks ?? []),
                  ...(importSummary.rccs ?? []),
                  ...(importSummary.vehicles ?? []),
                  ...(importSummary.drones ?? []),
                  ...(importSummary.optics ?? []),
                  ...(importSummary.sensors ?? []),
                  ...(importSummary.programs ?? []),
                  ...(importSummary.apps ?? []),
                ],
              ],
            ] as const
          ).map(([label, items]) => (
            <li key={label}>
              <details>
                <summary>
                  {ui(label)}: {items?.length ?? 0}
                </summary>
                <ul>
                  {items?.map((item, index) => (
                    <li key={index}>{itemName(item)}</li>
                  ))}
                </ul>
              </details>
            </li>
          ))}
        </ul>
      ) : null}
      {importSummary && !importReport ? <p>{ui("app.importReport.noWarnings")}</p> : null}
      <button className="btn" onClick={dismissImportReport}>
        {ui("app.importReport.dismiss")}
      </button>
    </ReviewPanel>
  );
}
