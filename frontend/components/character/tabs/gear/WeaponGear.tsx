"use client";
import { useState } from "react";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { accessoryFits, ammoFits, dropTree, weaponLine } from "@/lib/character/gear";
import { availBit, formatAccessoryCost, formatAmmoCost } from "@/lib/character/format";
import { removeWareTree } from "@/lib/character/ware";

export function WeaponGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.special_modification_limit?.max || 0) > 0 ? (
          <p className="muted">
            Special Modifications {d.special_modification_limit?.used || 0} /{" "}
            {d.special_modification_limit?.max}
          </p>
        ) : null}
        {(d.weapons || []).map((item) => {
          const installedNames = (item.accessories || []).map((acc) => acc.name);
          const parentCost = (catalog.weapons || []).find((row) => row.id === item.weapon_id)?.cost;
          const specialMod = d.special_modification_limit;
          const addons = (catalog.weapon_accessories || []).filter(
            (mod) =>
              accessoryFits(mod, item, installedNames, specialMod) &&
              !(item.accessories || []).some((acc) => acc.accessory_id === mod.id),
          );
          const ammoKey = `${item.id}-ammo`;
          const ammoAddons = (catalog.gear || []).filter(
            (mod) =>
              ammoFits(mod, item) && !(item.ammo_gear || []).some((row) => row.gear_id === mod.id),
          );
          const fromGear = Boolean(item.from_gear && item.source_gear_id);
          const fromWare = Boolean(item.from_ware && item.source_ware_id);
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {weaponLine(item)} / {item.nuyen.toLocaleString()}¥{availBit(item)}{" "}
                  / {item.source}
                  {fromGear ? ui("weapon.fromGear") : ""}
                  {fromWare ? ui("weapon.fromWare") : ""}
                  {item.limb_str != null ? ui("weapon.limbStr", { str: item.limb_str }) : ""}
                  {item.useskill ? ` / ${item.useskill}` : ""}
                  {item.focus_dice ? ui("weapon.focusDice", { dice: item.focus_dice }) : ""}
                  {item.category_dice
                    ? ui("weapon.categoryDice", { dice: item.category_dice })
                    : ""}
                  {item.mounted_label ? ui("weapon.mounted", { name: tr(item.mounted_label) }) : ""}
                </div>
                {fromWare ? null : (
                  <div className="cyber-controls">
                    <label>
                      {ui("common.qty")}
                      <input
                        type="number"
                        min={1}
                        value={item.qty}
                        onChange={(e) => {
                          const qty = Number(e.target.value);
                          if (fromGear) {
                            patch({
                              gear: (ch.gear || []).map((row) =>
                                row.id === item.source_gear_id ? { ...row, qty } : row,
                              ),
                            });
                            return;
                          }
                          patch({
                            weapons: (ch.weapons || []).map((row) =>
                              row.id === item.id ? { ...row, qty } : row,
                            ),
                          });
                        }}
                      />
                    </label>
                  </div>
                )}
                {(item.accessories || []).map((acc) => (
                  <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                    {tr(acc.name)}
                    {acc.mount ? ` / ${acc.mount}` : ""}
                    {acc.specialmodification
                      ? ` / ${ui("weapon.specialMod", { cost: acc.special_modification_cost || 1 })}`
                      : acc.included
                        ? ` / ${ui("common.included")}`
                        : ` / ${acc.nuyen.toLocaleString()}¥`}
                    {availBit(acc)}
                    {acc.included ? null : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          onClick={() =>
                            patch({
                              weapon_accessories: (ch.weapon_accessories || []).filter(
                                (row) => row.id !== acc.id,
                              ),
                            })
                          }
                        >
                          {ui("common.remove")}
                        </button>
                      </>
                    )}
                  </div>
                ))}
                {!fromGear && addons.length ? (
                  <div className="cyber-controls">
                    <select
                      aria-label={`${tr(item.name)}: ${ui("weapon.addAccessory")}`}
                      value={slotPick[item.id] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                      }
                    >
                      <option value="">{ui("weapon.addAccessory")}</option>
                      {addons
                        .filter((mod) => mod.specialmodification || mod.source === "SR5")
                        .map((mod) => (
                          <option key={mod.id} value={mod.id}>
                            {tr(mod.name)} (
                            {mod.specialmodification
                              ? ui("weapon.specialMod", {
                                  cost: mod.special_modification_cost || 1,
                                })
                              : formatAccessoryCost(mod.cost, parentCost)}
                            )
                          </option>
                        ))}
                    </select>
                    <button
                      className="btn"
                      disabled={!slotPick[item.id]}
                      onClick={() => {
                        const wareId = slotPick[item.id];
                        const spec = addons.find((mod) => mod.id === wareId);
                        if (!spec) return;
                        patch({
                          weapon_accessories: [
                            ...(ch.weapon_accessories || []),
                            { accessory_id: spec.id, parent_id: item.id },
                          ],
                        });
                        setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                      }}
                    >
                      {ui("common.install")}
                    </button>
                  </div>
                ) : null}
                {(item.ammo_gear || []).map((ammo) => (
                  <div className="muted" key={ammo.id} style={{ marginTop: 6 }}>
                    {tr(ammo.label || ammo.name)}
                    {ammo.loaded ? ui("weapon.loaded") : ""}
                    {ammo.qty > 1 ? ` ×${ammo.qty}` : ""}
                    {ammo.costfor
                      ? ui("weapon.rounds", {
                          count: (ammo.costfor * ammo.qty).toLocaleString(),
                        })
                      : ""}
                    {` / ${ammo.nuyen.toLocaleString()}¥`}{" "}
                    {(ammo.ammo_weapon_types || []).length > 0 && !ammo.loaded ? (
                      <button
                        className="btn"
                        onClick={() =>
                          patch({
                            weapons: (ch.weapons || []).map((row) =>
                              row.id === item.id ? { ...row, loaded_ammo_id: ammo.id } : row,
                            ),
                          })
                        }
                      >
                        {ui("weapon.load")}
                      </button>
                    ) : null}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          gear: dropTree(ch.gear || [], ammo.id),
                          weapons: (ch.weapons || []).map((row) =>
                            row.id === item.id && row.loaded_ammo_id === ammo.id
                              ? { ...row, loaded_ammo_id: undefined }
                              : row,
                          ),
                        })
                      }
                    >
                      {ui("common.remove")}
                    </button>
                    <label>
                      {ui("common.qty")}
                      <input
                        type="number"
                        min={1}
                        max={99}
                        value={ammo.qty}
                        onChange={(e) =>
                          patch({
                            gear: (ch.gear || []).map((row) =>
                              row.id === ammo.id ? { ...row, qty: Number(e.target.value) } : row,
                            ),
                          })
                        }
                      />
                    </label>
                  </div>
                ))}
                {!fromGear && ammoAddons.length ? (
                  <div className="cyber-controls">
                    <select
                      aria-label={`${tr(item.name)}: ${ui("weapon.addAmmo")}`}
                      value={slotPick[ammoKey] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [ammoKey]: e.target.value }))
                      }
                    >
                      <option value="">{ui("weapon.addAmmo")}</option>
                      {ammoAddons
                        .filter((mod) => mod.source === "SR5")
                        .map((mod) => (
                          <option key={mod.id} value={mod.id}>
                            {tr(mod.name)} ({formatAmmoCost(mod.cost, mod.costfor)})
                          </option>
                        ))}
                    </select>
                    <button
                      className="btn"
                      disabled={!slotPick[ammoKey]}
                      onClick={() => {
                        const wareId = slotPick[ammoKey];
                        const spec = ammoAddons.find((mod) => mod.id === wareId);
                        if (!spec) return;
                        patch({
                          gear: [
                            ...(ch.gear || []),
                            {
                              gear_id: spec.id,
                              rating: Math.max(1, spec.minrating || 1),
                              parent_id: item.id,
                            },
                          ],
                        });
                        setSlotPick((cur) => ({ ...cur, [ammoKey]: "" }));
                      }}
                    >
                      {ui("common.install")}
                    </button>
                  </div>
                ) : null}
              </div>
              <button
                className="btn danger"
                onClick={() => {
                  if (fromGear) {
                    patch({
                      gear: dropTree(ch.gear || [], item.source_gear_id || item.id),
                    });
                    return;
                  }
                  if (fromWare) {
                    patch({
                      cyberware: removeWareTree(ch.cyberware || [], item.source_ware_id || item.id),
                      weapon_accessories: (ch.weapon_accessories || []).filter(
                        (row) => row.parent_id !== item.id,
                      ),
                      gear: (ch.gear || []).filter((row) => row.parent_id !== item.id),
                    });
                    return;
                  }
                  patch({
                    weapons: (ch.weapons || []).filter((row) => row.id !== item.id),
                    weapon_accessories: (ch.weapon_accessories || []).filter(
                      (row) => row.parent_id !== item.id,
                    ),
                    gear: (ch.gear || []).filter((row) => row.parent_id !== item.id),
                  });
                }}
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })}
      </>

      <CatalogPicker
        items={catalog.weapons || []}
        label={ui("weapon.search")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / {weaponLine(item)} / {item.cost}¥ / {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) => {
          // a few "weapons" in the catalog are really a gear entry in disguise
          if (item.add_gear_id) {
            patch({ gear: [...(ch.gear || []), { gear_id: item.add_gear_id, qty: 1 }] });
            return;
          }
          patch({ weapons: [...(ch.weapons || []), { weapon_id: item.id, qty: 1 }] });
        }}
      />
    </>
  );
}
