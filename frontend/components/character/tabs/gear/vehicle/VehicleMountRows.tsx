"use client";
import { SlotPicker } from "@/components/character/tabs/gear/vehicle/SlotPicker";
import type { VehicleRowProps } from "@/components/character/tabs/gear/vehicle/types";
import { useBookFilter } from "@/lib/character/books";
import { vehicleFits } from "@/lib/character/gear";

/** The weapon mounts on one vehicle, what is mounted in each, and the picker
 *  that bolts on another mount of a given size. */
export function VehicleMountRows({
  item,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  slotPick,
  setSlotPick,
}: VehicleRowProps) {
  const byBook = useBookFilter();
  const sizes = (catalog.weapon_mounts || []).filter(
    // Chummer's `BookXPath` hides the drone sizes unless `<dronemods>` is on
    (mod) =>
      mod.category === "Size" &&
      (d.drone_mods || !mod.optionaldrone) &&
      vehicleFits(mod.required, item),
  );
  // a weapon is available to mount unless it is already carried or in another
  // mount on this vehicle
  const mountedIds = new Set(
    (item.weapon_mounts || []).map((row) => row.weapon_install_id).filter(Boolean),
  );
  const freeWeapons = (d.weapons || []).filter(
    (weapon) => !weapon.mounted_on && !mountedIds.has(weapon.id),
  );
  return (
    <>
      {(item.weapon_mounts || []).map((mount) => (
        <div className="muted" key={mount.id} style={{ marginTop: 6 }}>
          {tr(mount.label || mount.name)}
          {mount.included ? ` / ${ui("common.included")}` : ` / ${mount.nuyen.toLocaleString()}¥`}
          {mount.slots ? ui("veh.slotCost", { slots: mount.slots }) : ""}
          {mount.weapon_name ? ` / ${tr(mount.weapon_name)}` : ui("veh.noWeapon")}
          {mount.included ? null : (
            <>
              {" "}
              <button
                className="btn danger"
                onClick={() =>
                  patch({
                    weapon_mounts: (ch.weapon_mounts || []).filter((row) => row.id !== mount.id),
                  })
                }
              >
                {ui("common.remove")}
              </button>
            </>
          )}
          <div className="cyber-controls">
            <select
              aria-label={`${tr(mount.name)}: ${ui("veh.mountWeapon")}`}
              value={mount.weapon_install_id || ""}
              onChange={(e) =>
                patch({
                  weapon_mounts: (ch.weapon_mounts || []).map((row) =>
                    row.id === mount.id
                      ? { ...row, weapon_install_id: e.target.value || null }
                      : row,
                  ),
                })
              }
            >
              <option value="">{ui("veh.mountWeapon")}</option>
              {mount.weapon_install_id && mount.weapon_name ? (
                <option value={mount.weapon_install_id}>{tr(mount.weapon_name)}</option>
              ) : null}
              {freeWeapons.map((weapon) => (
                <option key={weapon.id} value={weapon.id}>
                  {tr(weapon.name)}
                </option>
              ))}
            </select>
          </div>
        </div>
      ))}
      <SlotPicker
        pickKey={`${item.id}-mount`}
        rowName={tr(item.name)}
        label={ui("veh.addMount")}
        options={byBook(sizes)}
        onAdd={(spec) =>
          patch({
            weapon_mounts: [...(ch.weapon_mounts || []), { size_id: spec.id, parent_id: item.id }],
          })
        }
        tr={tr}
        ui={ui}
        slotPick={slotPick}
        setSlotPick={setSlotPick}
      />
    </>
  );
}
