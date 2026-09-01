import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function MartialSection(s: SheetData) {
  const { tr, d } = s;
  return (
    <Section title="武道" empty={!(d.martial_arts || []).length}>
      <ul className="sheet-list">
        {(d.martial_arts || []).map((art) => (
          <li key={art.id}>
            <b>{tr(art.name)}</b>
            {art.free ? " ★" : ""}
            {(art.techniques || []).length
              ? ` ・ ${art.techniques.map((t) => tr(t.name)).join("、")}`
              : " ・ 技未選択"}
          </li>
        ))}
      </ul>
    </Section>
  );
}
