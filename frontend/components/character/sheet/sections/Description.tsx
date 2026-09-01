import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function DescriptionSection(s: SheetData) {
  const { character } = s;
  const stats: [string, string][] = (
    [
      ["年齢", character.age],
      ["性別", character.sex],
      ["身長", character.height],
      ["体重", character.weight],
      ["目", character.eyes],
      ["髪", character.hair],
      ["肌", character.skin],
      ["コンセプト", character.concept],
    ] as [string, string | undefined][]
  ).filter((r): r is [string, string] => Boolean((r[1] || "").trim()));
  const blocks: [string, string][] = (
    [
      ["容姿", character.appearance],
      ["背景", character.background],
      ["メモ", character.notes],
    ] as [string, string | undefined][]
  ).filter((r): r is [string, string] => Boolean((r[1] || "").trim()));
  if (!stats.length && !blocks.length && !character.portrait) return null;
  return (
    <Section title="記述">
      {character.portrait || stats.length ? (
        <div className="sheet-portrait-row">
          {character.portrait ? (
            <img className="sheet-portrait" src={character.portrait} alt="ポートレート" />
          ) : null}
          {stats.length ? (
            <div className="sheet-derived-grid sheet-vehicle-stats">
              {stats.map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <b>{value}</b>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      {blocks.map(([label, value]) => (
        <div key={label} className="sheet-block">
          <h4>{label}</h4>
          <p className="sheet-notes">{value}</p>
        </div>
      ))}
    </Section>
  );
}
