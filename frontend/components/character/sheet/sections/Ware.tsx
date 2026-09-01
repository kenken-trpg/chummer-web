import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function WareSection(s: SheetData) {
  const { tr, d, cyber, bio } = s;
  return (
    <Section title="ウェア" empty={!cyber.length && !bio.length}>
      {cyber.length ? (
        <div className="sheet-block">
          <h4>サイバーウェア（ESS −{d.essence_lost_cyber ?? 0}）</h4>
          {d.limb_replace ? (
            <p className="sheet-note">
              サイバーリム平均: STR {d.limb_replace.str} / AGI {d.limb_replace.agi}
              （リム {d.limb_replace.count}/{d.limb_replace.parts}・肉 STR {d.limb_replace.meat_str}{" "}
              / AGI {d.limb_replace.meat_agi}）
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
                    肢 STR {item.limb_str} / AGI {item.limb_agi}
                    {(item.limb_armor ?? 0) > 0 ? ` / 装甲 ${item.limb_armor}` : ""}
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
          <h4>バイオウェア（ESS −{d.essence_lost_bio ?? 0}）</h4>
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
