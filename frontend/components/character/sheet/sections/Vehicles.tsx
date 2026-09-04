import type { SheetData } from "@/lib/character/sheet-data";
import { Section, VehicleBlock } from "@/components/character/sheet/blocks";

export function VehiclesSection(s: SheetData) {
  const { d, tr } = s;
  return (
    <Section title="sheet.vehicles" empty={!(d.vehicles || []).length && !(d.drones || []).length}>
      {(d.vehicles || []).map((v) => (
        <VehicleBlock key={v.id} v={v} tr={tr} />
      ))}
      {(d.drones || []).map((v) => (
        <VehicleBlock key={v.id} v={v} tr={tr} />
      ))}
    </Section>
  );
}
