import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { rangeNameFor, rangeRow, resolveDamageStr } from "@/lib/character/sheet-format";
import { Fragment } from "react";
import { useUiText } from "@/lib/i18n";

export function CombatSection(s: SheetData) {
  const { catalog, tr, d, totals, weapons, armors } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.combat" empty={!weapons.length && !armors.length && !d.worn_armor}>
      {armors.length || d.worn_armor ? (
        <div className="sheet-block">
          <h4>{ui("sheet.armorBlock")}</h4>
          <ul className="sheet-list">
            {(armors.length ? armors : []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}
                {item.armor_value}
                {item.equipped ? ui("sheet.equipped") : ""}
                {item.has_wireless && item.wireless === false ? ui("sheet.wirelessOff") : ""}
                {(item.mods || []).length
                  ? ` ${ui("common.termSep")} ${(item.mods || [])
                      .map(
                        (m) =>
                          `${tr(m.name)}${
                            m.has_wireless && m.wireless === false
                              ? ui("sheet.wirelessOffShort")
                              : ""
                          }`,
                      )
                      .join(ui("common.listSep"))}`
                  : ""}
              </li>
            ))}
            {!armors.length && d.worn_armor ? (
              <li>
                <b>{tr(d.worn_armor)}</b>
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
      {weapons.length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.weapons")}</h4>
          <table className="sheet-table sheet-table--weapon">
            <thead>
              <tr>
                <th>{ui("sheet.col.weapon")}</th>
                <th>Acc</th>
                <th>DV</th>
                <th>AP</th>
                <th>{ui("sheet.col.mode")}</th>
                <th>RC</th>
                <th>{ui("sheet.col.ammo")}</th>
                <th>{ui("sheet.col.reach")}</th>
                <th>{ui("sheet.col.conceal")}</th>
              </tr>
            </thead>
            <tbody>
              {weapons.map((item) => {
                const dash = (v?: string) => (v && v !== "0" && v !== "-" ? v : "–");
                const thrown = (item.useskill || "") === "Throwing Weapons";
                const dv = thrown
                  ? resolveDamageStr(item.damage, (totals.STR || 0) + (d.throw_str || 0))
                  : item.damage;
                const sub = [
                  (item.accessories || []).map((a) => tr(a.name)).join(ui("common.listSep")),
                  (item.focus_dice || 0) > 0
                    ? ui("sheet.weaponFocus", { dice: item.focus_dice ?? 0 })
                    : "",
                  (item.category_dice || 0) > 0
                    ? ui("sheet.categoryDice", { dice: item.category_dice ?? 0 })
                    : "",
                  item.mounted_label ? ui("sheet.mountedOn", { name: tr(item.mounted_label) }) : "",
                ]
                  .filter(Boolean)
                  .join(` ${ui("common.termSep")} `);
                return (
                  <Fragment key={item.id}>
                    <tr>
                      <td className="left">
                        {tr(item.name)}
                        {item.qty > 1 ? ` ×${item.qty}` : ""}
                      </td>
                      <td>{dash(item.accuracy)}</td>
                      <td>{dash(dv)}</td>
                      <td>{item.ap && item.ap !== "0" ? item.ap : "–"}</td>
                      <td>{dash(item.mode)}</td>
                      <td>{dash(item.rc)}</td>
                      <td>{dash(item.ammo)}</td>
                      <td>{dash(item.reach)}</td>
                      <td>{dash(item.conceal)}</td>
                    </tr>
                    {sub ? (
                      <tr className="sheet-subrow">
                        <td className="left" colSpan={9}>
                          {sub}
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
          {(() => {
            const table = catalog.weapon_ranges || {};
            const str = totals.STR || 0;
            const throwBonus = d.throw_range_str || 0;
            const names: string[] = [];
            const thrownNames = new Set<string>();
            for (const w of weapons) {
              if ((w.type || "") === "Melee") continue;
              const isThrown = (w.useskill || "") === "Throwing Weapons";
              for (const n of [rangeNameFor(w), (w.alt_range || "").trim()]) {
                if (!n || !table[n]) continue;
                if (!names.includes(n)) names.push(n);
                if (isThrown) thrownNames.add(n);
              }
            }
            if (!names.length) return null;
            const strScaled = names.some((n) => /\{STR\}/i.test(JSON.stringify(table[n])));
            const throwApplies = throwBonus > 0 && [...thrownNames].some((n) => names.includes(n));
            return (
              <table className="sheet-table sheet-table--range">
                <thead>
                  <tr>
                    <th>
                      {ui("sheet.rangeHeader")}
                      {strScaled ? ui("sheet.rangeStr", { str }) : ""}
                      {throwApplies ? ui("sheet.rangeThrown", { str: str + throwBonus }) : ""}
                    </th>
                    <th>{ui("sheet.range.short")}</th>
                    <th>{ui("sheet.range.medium")}</th>
                    <th>{ui("sheet.range.long")}</th>
                    <th>{ui("sheet.range.extreme")}</th>
                  </tr>
                </thead>
                <tbody>
                  {names.map((name) => {
                    const cells = rangeRow(
                      table[name],
                      str + (thrownNames.has(name) ? throwBonus : 0),
                    );
                    return (
                      <tr key={name}>
                        <td className="left">{tr(name)}</td>
                        {cells.map((c, i) => (
                          <td key={i}>{c}</td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            );
          })()}
          {(() => {
            const rc = d.recoil;
            const ranged = weapons.filter(
              (w) => (w.type || "") !== "Melee" && (w.mode || "").trim(),
            );
            if (!rc || !ranged.length) return null;
            // net dice penalty for firing `rounds` bullets in one phase, after RC
            const pen = (rounds: number, rcTotal: number) => Math.max(0, rounds - 1 - rcTotal);
            const modeCols: [string, number, RegExp][] = [
              ["SA×2", 2, /SA/],
              ["BF", 3, /BF/],
              ["FA(6)", 6, /FA/],
              [ui("sheet.fullAuto"), 10, /FA/],
            ];
            return (
              <>
                <table className="sheet-table sheet-table--range">
                  <thead>
                    <tr>
                      <th>{ui("sheet.recoilHeader")}</th>
                      <th>{ui("sheet.recoilTotal")}</th>
                      {modeCols.map(([label]) => (
                        <th key={label}>{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {ranged.map((w) => {
                      const rcTotal = w.rc_total ?? 0;
                      return (
                        <tr key={w.id}>
                          <td className="left">{tr(w.name)}</td>
                          <td>{rcTotal}</td>
                          {modeCols.map(([label, rounds, re]) => (
                            <td key={label}>
                              {re.test(w.mode || "")
                                ? pen(rounds, rcTotal)
                                  ? `−${pen(rounds, rcTotal)}`
                                  : "±0"
                                : "–"}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <p className="sheet-note">
                  {ui("sheet.recoilNote", { str: rc.str, strRc: rc.str_rc })}
                </p>
              </>
            );
          })()}
        </div>
      ) : null}
    </Section>
  );
}
