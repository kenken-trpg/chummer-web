import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function MiscGearSection(s: SheetData) {
  const { tr, gearMisc } = s;
  return (
    <Section title="sheet.miscGear" empty={!gearMisc.length}>
      <ul className="sheet-list sheet-list-compact">
        {gearMisc.map((item) => (
          <li key={item.id}>
            {tr(item.name)}
            {item.rating > 1 ? ` R${item.rating}` : ""}
            {(item.qty || 1) > 1 ? ` ×${item.qty}` : ""}
          </li>
        ))}
      </ul>
    </Section>
  );
}
