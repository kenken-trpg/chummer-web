import { useUiText } from "@/lib/i18n";
import type { SheetData } from "@/lib/character/sheet-data";
import { Section, VehicleBlock } from "@/components/character/sheet/blocks";

export function VehiclesSection(s: SheetData) {
  const { d, tr } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.vehicles" empty={!(d.vehicles || []).length && !(d.drones || []).length}>
      {[...(d.vehicles || []), ...(d.drones || [])].map((v) => {
        const implants = (d.weapons || []).filter((w) => w.vehicle_id === v.id);
        return (
          <div key={v.id}>
            <VehicleBlock v={v} tr={tr} />
            {implants.length ? (
              <p className="sheet-note">
                {ui("weapon.vehicleInventory", {
                  list: implants.map((w) => tr(w.name)).join(ui("common.listSep")),
                })}
              </p>
            ) : null}
          </div>
        );
      })}
    </Section>
  );
}
