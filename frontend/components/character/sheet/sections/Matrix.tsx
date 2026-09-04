import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { matrixCM } from "@/lib/character/format";
import { useUiText } from "@/lib/i18n";

export function MatrixSection(s: SheetData) {
  const { tr, d } = s;
  const { ui } = useUiText();
  return (
    <Section
      title="sheet.matrix"
      empty={!d.commlink && !d.cyberdeck && !d.rcc && !d.living_persona}
    >
      {(() => {
        const rows: {
          key: string;
          label: string;
          dr: number;
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
            dp: d.commlink.dataprocessing,
            fw: d.commlink.firewall,
          });
        if (d.cyberdeck) {
          const ck = d.cyberdeck;
          rows.push({
            key: "cd",
            label: ui("sheet.deviceDeck", { name: tr(ck.name) }),
            dr: ck.device_rating,
            a: ck.attack,
            s: ck.sleaze,
            dp: ck.dataprocessing,
            fw: ck.firewall,
            prog: ck.program_max != null ? `${ck.program_used ?? 0}/${ck.program_max}` : undefined,
            order: ck.can_reorder && ck.array_order ? ck.array_order.join(" ▸ ") : undefined,
          });
        }
        if (d.rcc)
          rows.push({
            key: "rcc",
            label: ui("sheet.deviceRcc", { name: tr(d.rcc.name) }),
            dr: d.rcc.device_rating,
            dp: d.rcc.dataprocessing,
            fw: d.rcc.firewall,
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
            init:
              (lp.matrix_initiative_dice || 0) > 0 ? `+${lp.matrix_initiative_dice}d6` : undefined,
          });
        }
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
                  <th>Prog</th>
                  <th>M.CM</th>
                  <th>M.Init</th>
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
                    <td>{matrixCM(r.dr)}</td>
                    <td>{r.init ?? "–"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
    </Section>
  );
}
