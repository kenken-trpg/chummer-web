"use client";
import { PriceField } from "@/components/character/tabs/gear/PriceField";
import { AddonSelect } from "@/components/character/AddonSelect";
import { ArmorModRow, CarriedGearRow } from "@/components/character/tabs/gear/ArmorRows";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { armorModFits } from "@/lib/character/gear";
import {
  availBit,
  formatAccessoryCost,
  mergeSpecialArmor,
  specialArmorLine,
} from "@/lib/character/format";

/** The other pieces a Custom Fit (Stack) can be tailored to: whole armors
 * (not `+N` accessories), by catalog name, keeping the current pick even
 * when that armor has since been sold. */
function stackTargets(
  items: { id: string; name: string; additive?: boolean }[],
  selfId: string,
  current?: string,
): string[] {
  const names = items.filter((row) => row.id !== selfId && !row.additive).map((row) => row.name);
  if (current) names.push(current);
  return [...new Set(names)];
}

export function ArmorGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  // what says the capacity it takes in armor (`<armorcapacity>`): gear, a
  // helmet's vision / audio enhancements, a sensor housing (its functions go
  // in the housing, not the armor)
  const carriable = [
    ...(catalog.gear || []).map((row) => ({ ...row, bucket: "gear" as const })),
    ...(catalog.optics || []).map((row) => ({ ...row, bucket: "optics" as const })),
    ...(catalog.sensors || [])
      .filter((row) => row.category === "Sensors")
      .map((row) => ({ ...row, bucket: "sensors" as const })),
  ].filter((row) => row.armor_capacity);
  return (
    <>
      <>
        {(d.armor_items || []).map((item) => {
          const installedNames = (item.mods || []).map((mod) => mod.name);
          const parentCost = (catalog.armor || []).find((row) => row.id === item.armor_id)?.cost;
          const addons = (catalog.armor_mods || []).filter(
            (mod) =>
              armorModFits(mod, item, installedNames) &&
              !(item.mods || []).some(
                (row) => row.mod_id === mod.id || (mod.unique && row.unique === mod.unique),
              ),
          );
          const specialLine = specialArmorLine(mergeSpecialArmor(item.mods), ui);
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {ui("armor.value", { value: item.armor_value })}
                  {item.equipped
                    ? ui("armor.contributes", { value: item.contributes ?? 0 })
                    : ui("armor.notEquipped")}
                  {specialLine ? ` / ${specialLine}` : ""}
                  {availBit(item, ui)}
                  {item.capacity_max
                    ? ui("gear.capacity", {
                        used: item.capacity_used ?? 0,
                        max: item.capacity_max,
                      })
                    : ""}
                  {" / "}
                  {item.nuyen.toLocaleString()}¥ / {item.source}
                </div>
                <div className="cyber-controls">
                  <DiscountToggle list="armor" id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
                  <PriceField
                    range={item.cost_range}
                    value={
                      (ch.armor || []).find((row) => row.id === item.id)?.cost ??
                      item.cost_range?.[0] ??
                      0
                    }
                    label={tr(item.name)}
                    ui={ui}
                    onChange={(cost) =>
                      patch({
                        armor: (ch.armor || []).map((row) =>
                          row.id === item.id ? { ...row, cost } : row,
                        ),
                      })
                    }
                  />
                  <label>
                    <input
                      type="checkbox"
                      checked={item.equipped}
                      onChange={(e) =>
                        patch({
                          armor: (ch.armor || []).map((row) =>
                            row.id === item.id ? { ...row, equipped: e.target.checked } : row,
                          ),
                        })
                      }
                    />
                    {ui("common.equipped")}
                  </label>
                  {item.rating_max > 0 ? (
                    <label>
                      Rating
                      <input
                        type="number"
                        min={1}
                        max={item.rating_max}
                        value={item.rating}
                        onChange={(e) =>
                          patch({
                            armor: (ch.armor || []).map((row) =>
                              row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                            ),
                          })
                        }
                      />
                    </label>
                  ) : null}
                  {item.has_wireless ? (
                    <label title={ui("common.wirelessHint")}>
                      <input
                        type="checkbox"
                        checked={item.wireless ?? true}
                        onChange={(e) =>
                          patch({
                            armor: (ch.armor || []).map((row) =>
                              row.id === item.id ? { ...row, wireless: e.target.checked } : row,
                            ),
                          })
                        }
                      />
                      {ui("common.wireless")}
                    </label>
                  ) : null}
                </div>
                {(item.mods || []).map((mod) => (
                  <ArmorModRow
                    key={mod.id}
                    mod={mod}
                    stackOptions={stackTargets(d.armor_items || [], item.id, mod.stack_with)}
                    character={ch}
                    tr={tr}
                    ui={ui}
                    patch={patch}
                  />
                ))}
                {(item.gear || []).map((gear) => (
                  <CarriedGearRow
                    key={gear.id}
                    gear={gear}
                    character={ch}
                    tr={tr}
                    ui={ui}
                    patch={patch}
                  />
                ))}
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt={ui("gear.addArmorGear")}
                  addLabel={ui("gear.putIn")}
                  tr={tr}
                  options={carriable}
                  optionLabel={(row) => `${tr(row.name)} ${row.armor_capacity} (${row.cost}¥)`}
                  onAdd={(row) =>
                    patch({
                      [row.bucket]: [
                        ...(ch[row.bucket] || []),
                        {
                          gear_id: row.id,
                          parent_id: item.id,
                          rating: Math.max(1, row.minrating || 1),
                          ...(row.bucket === "gear" ? { qty: 1 } : {}),
                        },
                      ],
                    })
                  }
                />
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt={ui("gear.addMod")}
                  tr={tr}
                  // `armorModFits` has already decided what can go on this
                  // piece, so every option here is buyable. (It used to hide
                  // non-SR5 mods unless the *catalog search box* below had text
                  // in it — an invisible coupling between two unrelated
                  // controls.) Cost is relative to the parent, hence the label.
                  options={addons}
                  optionLabel={(mod) =>
                    `${tr(mod.name)} (${formatAccessoryCost(mod.cost, parentCost)})`
                  }
                  onAdd={(mod) =>
                    patch({
                      armor_mods: [
                        ...(ch.armor_mods || []),
                        {
                          mod_id: mod.id,
                          parent_id: item.id,
                          rating: Math.max(1, mod.minrating || 1),
                        },
                      ],
                    })
                  }
                />
              </div>
              <button
                className="btn danger"
                aria-label={ui("common.deleteLabel", { name: tr(item.name) })}
                onClick={() =>
                  patch({
                    armor: (ch.armor || []).filter((row) => row.id !== item.id),
                    armor_mods: (ch.armor_mods || []).filter((row) => row.parent_id !== item.id),
                    // what is carried in it, and what hangs off that
                    ...Object.fromEntries(
                      (["gear", "optics", "sensors"] as const).map((key) => {
                        const inside = new Set(
                          (ch[key] || [])
                            .filter((row) => row.parent_id === item.id)
                            .map((row) => row.id),
                        );
                        return [
                          key,
                          (ch[key] || []).filter(
                            (row) => row.parent_id !== item.id && !inside.has(row.parent_id || ""),
                          ),
                        ];
                      }),
                    ),
                  })
                }
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })}
      </>

      <CatalogPicker
        items={catalog.armor || []}
        label={ui("gear.searchArmor")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / {ui("armor.value", { value: item.armor })} / {item.cost}¥ /{" "}
            {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            armor: [
              ...(ch.armor || []),
              { armor_id: item.id, rating: Math.max(1, item.minrating || 1), equipped: true },
            ],
          })
        }
      />
    </>
  );
}
