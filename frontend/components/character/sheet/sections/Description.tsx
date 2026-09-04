import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { type MsgKey, useUiText } from "@/lib/i18n";

export function DescriptionSection(s: SheetData) {
  const { character } = s;
  const { ui } = useUiText();
  const stats: [MsgKey, string][] = (
    [
      ["desc.age", character.age],
      ["desc.sex", character.sex],
      ["desc.height", character.height],
      ["desc.weight", character.weight],
      ["desc.eyes", character.eyes],
      ["desc.hair", character.hair],
      ["desc.skin", character.skin],
      ["desc.concept", character.concept],
    ] as [MsgKey, string | undefined][]
  ).filter((r): r is [MsgKey, string] => Boolean((r[1] || "").trim()));
  const blocks: [MsgKey, string][] = (
    [
      ["desc.appearance", character.appearance],
      ["desc.background", character.background],
      ["desc.notes", character.notes],
    ] as [MsgKey, string | undefined][]
  ).filter((r): r is [MsgKey, string] => Boolean((r[1] || "").trim()));
  if (!stats.length && !blocks.length && !character.portrait) return null;
  return (
    <Section title="desc.title">
      {character.portrait || stats.length ? (
        <div className="sheet-portrait-row">
          {character.portrait ? (
            <img className="sheet-portrait" src={character.portrait} alt={ui("desc.portraitAlt")} />
          ) : null}
          {stats.length ? (
            <div className="sheet-derived-grid sheet-vehicle-stats">
              {stats.map(([label, value]) => (
                <div key={label}>
                  <span>{ui(label)}</span>
                  <b>{value}</b>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      {blocks.map(([label, value]) => (
        <div key={label} className="sheet-block">
          <h4>{ui(label)}</h4>
          <p className="sheet-notes">{value}</p>
        </div>
      ))}
    </Section>
  );
}
