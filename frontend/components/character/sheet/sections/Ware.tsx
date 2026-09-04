import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function WareSection(s: SheetData) {
  const { tr, d, cyber, bio } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.ware" empty={!cyber.length && !bio.length}>
      {cyber.length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.cyberware", { lost: d.essence_lost_cyber ?? 0 })}</h4>
          {d.limb_replace ? (
            <p className="sheet-note">
              {ui("sheet.limbAverage", {
                str: d.limb_replace.str,
                agi: d.limb_replace.agi,
                count: d.limb_replace.count,
                parts: d.limb_replace.parts,
                meatStr: d.limb_replace.meat_str,
                meatAgi: d.limb_replace.meat_agi,
              })}
            </p>
          ) : null}
          <ul className="sheet-list">
            {cyber.map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {item.rating > 1 ? ` R${item.rating}` : ""}
                {item.grade && item.grade !== "Standard" ? ` / ${item.grade}` : ""}
                {item.side ? ` / ${item.side}` : ""}
                {item.limb_str != null ? (
                  <span className="sheet-dim">
                    {" "}
                    {ui("sheet.limb", { str: item.limb_str, agi: item.limb_agi ?? 0 })}
                    {(item.limb_armor ?? 0) > 0
                      ? ui("sheet.limbArmor", { armor: item.limb_armor ?? 0 })
                      : ""}
                  </span>
                ) : null}
                <span className="sheet-dim"> ESS −{item.essence}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {bio.length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.bioware", { lost: d.essence_lost_bio ?? 0 })}</h4>
          <ul className="sheet-list">
            {bio.map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {item.rating > 1 ? ` R${item.rating}` : ""}
                {item.grade && item.grade !== "Standard" ? ` / ${item.grade}` : ""}
                <span className="sheet-dim"> ESS −{item.essence}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}
