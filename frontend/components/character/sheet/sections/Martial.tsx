import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function MartialSection(s: SheetData) {
  const { tr, d } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.martial" empty={!(d.martial_arts || []).length}>
      <ul className="sheet-list">
        {(d.martial_arts || []).map((art) => (
          <li key={art.id}>
            <b>{tr(art.name)}</b>
            {art.free ? " ★" : ""}
            {(art.techniques || []).length
              ? ` ${ui("common.termSep")} ${art.techniques
                  .map((t) => tr(t.name))
                  .join(ui("common.listSep"))}`
              : ui("sheet.noTechnique")}
          </li>
        ))}
      </ul>
    </Section>
  );
}
