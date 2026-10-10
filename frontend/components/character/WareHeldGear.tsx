"use client";

import { AddonSelect } from "@/components/character/AddonSelect";
import { CarriedGearRow } from "@/components/character/tabs/gear/ArmorRows";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import type { InstalledWare } from "@/lib/types";

/**
 * What a piece of ware holds — a Chemical Gland's chemical, an Auto
 * Injector's drug — and the select to put one in. Only the categories its
 * `<allowgear>` names are offered; Chummer prices the gland by what is in it.
 */
export function WareHeldGear({
  item,
  catalog,
  character: ch,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "tr" | "ui" | "patch"> & { item: InstalledWare }) {
  const allowed = item.allow_gear || [];
  if (!allowed.length) return null;
  const options = (catalog.gear || []).filter(
    (row) => allowed.includes(row.category) && row.category !== "Custom",
  );
  return (
    <>
      <div className="muted" style={{ marginTop: 6 }}>
        <HelpTip
          label={ui("help.open", { label: ui("help.heldGear.statsLabel") })}
          lines={[{ label: ui("help.heldGear.what") }, { label: ui("help.gear.qty") }]}
        >
          {ui("help.heldGear.statsLabel")}
        </HelpTip>
      </div>
      {item.modular_equipped === false && (item.gear || []).length > 0 ? (
        <p className="muted">{ui("ware.heldGearInactive")}</p>
      ) : null}
      {(item.gear || []).map((gear) => (
        <CarriedGearRow key={gear.id} gear={gear} character={ch} tr={tr} ui={ui} patch={patch} />
      ))}
      {item.included || item.granted_by ? null : (
        <AddonSelect
          rowName={tr(item.name)}
          prompt={ui("ware.addHeldGear")}
          addLabel={ui("gear.putIn")}
          tr={tr}
          options={options}
          onAdd={(row) =>
            patch({
              gear: [
                ...(ch.gear || []),
                {
                  gear_id: row.id,
                  parent_id: item.id,
                  rating: Math.max(1, row.minrating || 1),
                  qty: 1,
                },
              ],
            })
          }
        />
      )}
    </>
  );
}
