import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { matrixCM } from "@/lib/character/format";
import { useUiText } from "@/lib/i18n";
import { scopeTr } from "@/lib/ui-strings";

export function MatrixSection(s: SheetData) {
  const { tr: sheetTr, d } = s;
  const tr = scopeTr(sheetTr, "gear");
  const { ui } = useUiText();
  const mi = d.matrix_initiative;
  // Only the persona the character actually runs has a VR initiative; the
  // other devices in the table are just kit they own.
  const initFor = (device: string) =>
    mi && mi.device === device
      ? ui("sheet.matrixInit", {
          cold: `${mi.value}+${mi.cold_dice}d6`,
          hot: `${mi.value}+${mi.hot_dice}d6`,
        })
      : undefined;
  const programs = d.ai_programs || [];
  return (
    <Section
      title="sheet.matrix"
      empty={!d.commlink && !d.cyberdeck && !d.rcc && !d.living_persona && !programs.length}
    >
      {(() => {
        const rows: {
          key: string;
          label: string;
          dr: number;
          cm?: number;
          a?: number;
          s?: number;
          dp: number;
          fw: number;
          prog?: string;
          init?: string;
          order?: string;
        }[] = [];
        if (d.commlink)
          rows.push({
            key: "cl",
            label: ui("sheet.deviceCommlink", { name: tr(d.commlink.name) }),
            dr: d.commlink.device_rating,
            cm: d.commlink.matrix_condition_monitor,
            a: d.commlink.attack || undefined,
            s: d.commlink.sleaze || undefined,
            dp: d.commlink.dataprocessing,
            fw: d.commlink.firewall,
            init: initFor("commlink"),
          });
        if (d.cyberdeck) {
          const ck = d.cyberdeck;
          rows.push({
            key: "cd",
            label: ui("sheet.deviceDeck", { name: tr(ck.name) }),
            dr: ck.device_rating,
            cm: ck.matrix_condition_monitor,
            a: ck.attack,
            s: ck.sleaze,
            dp: ck.dataprocessing,
            fw: ck.firewall,
            prog:
              ck.program_max != null
                ? ui("gear.programRunningCount", {
                    used: ck.program_used ?? 0,
                    max: ck.program_max,
                  })
                : undefined,
            order: ck.can_reorder && ck.array_order ? ck.array_order.join(" ▸ ") : undefined,
            init: initFor("cyberdeck"),
          });
        }
        if (d.rcc)
          rows.push({
            key: "rcc",
            label: ui("sheet.deviceRcc", { name: tr(d.rcc.name) }),
            dr: d.rcc.device_rating,
            cm: d.rcc.matrix_condition_monitor,
            dp: d.rcc.dataprocessing,
            fw: d.rcc.firewall,
            init: initFor("rcc"),
          });
        if (d.living_persona) {
          const lp = d.living_persona;
          rows.push({
            key: "lp",
            label: ui("sheet.livingPersona"),
            dr: lp.device_rating,
            a: lp.attack,
            s: lp.sleaze,
            dp: lp.dataprocessing,
            fw: lp.firewall,
            init: initFor("living_persona"),
          });
        }
        if (!rows.length) return null;
        return (
          <>
            <table className="sheet-table sheet-table--matrix">
              <thead>
                <tr>
                  <th>{ui("sheet.col.device")}</th>
                  <th>DR</th>
                  <th>A</th>
                  <th>S</th>
                  <th>DP</th>
                  <th>FW</th>
                  <th>{ui("sheet.col.programs")}</th>
                  <th>{ui("sheet.col.matrixCm")}</th>
                  <th>{ui("sheet.col.matrixInit")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <td className="left">{r.label}</td>
                    <td>{r.dr}</td>
                    <td>{r.a ?? "–"}</td>
                    <td>{r.s ?? "–"}</td>
                    <td>{r.dp}</td>
                    <td>{r.fw}</td>
                    <td>{r.prog ?? "–"}</td>
                    <td>{r.cm ?? matrixCM(r.dr)}</td>
                    <td>{r.init ?? "–"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {mi ? <p className="sheet-note">{ui("sheet.matrixInitNote")}</p> : null}
            {rows.some((r) => r.order) ? (
              <p className="sheet-note">
                {rows
                  .filter((r) => r.order)
                  .map((r) => `${r.label}: ${r.order}`)
                  .join(" ／ ")}
              </p>
            ) : null}
          </>
        );
      })()}
      {programs.length ? (
        // an A.I.'s own programs, not the ones its devices run
        <div className="sheet-block">
          <h4>{ui("sheet.aiPrograms")}</h4>
          <ul className="sheet-list">
            {programs.map((row) => (
              <li key={row.id}>
                <b>{sheetTr(row.name)}</b>
                {row.extra ? `（${sheetTr(row.extra)}）` : ""}
                {row.free ? ui("sheet.aiProgramFree", { name: sheetTr(row.granted_by) }) : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}
