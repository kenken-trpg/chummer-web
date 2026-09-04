"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { armorModFits } from "@/lib/character/gear";
import {
  availBit,
  formatAccessoryCost,
  limitModifierLine,
  mergeSpecialArmor,
  specialArmorLine,
} from "@/lib/character/format";

export function ArmorGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
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
          const specialLine = specialArmorLine(mergeSpecialArmor(item.mods));
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / 装甲 {item.armor_value}
                  {item.equipped ? ` ・ 加算 ${item.contributes}` : " ・ 未装備"}
                  {specialLine ? ` / ${specialLine}` : ""}
                  {availBit(item)}
                  {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                  {" / "}
                  {item.nuyen.toLocaleString()}¥ / {item.source}
                </div>
                <div className="cyber-controls">
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
                    装備
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
                    <label title="ワイヤレス機能を有効化してボーナスを反映">
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
                      ワイヤレス
                    </label>
                  ) : null}
                </div>
                {(item.mods || []).map((mod) => (
                  <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
                    {tr(mod.name)}
                    {mod.rating_max > 1 ? ` R${mod.rating}` : ""}
                    {mod.included ? " / 付属" : ` / ${mod.nuyen.toLocaleString()}¥`}
                    {mod.capacity_cost
                      ? ` / 容量 ${mod.capacity_cost < 0 ? `+${-mod.capacity_cost}` : mod.capacity_cost}`
                      : ""}
                    {specialArmorLine(mod.special_armor)
                      ? ` / ${specialArmorLine(mod.special_armor)}`
                      : ""}
                    {limitModifierLine(mod.limit_modifiers)
                      ? ` / ${limitModifierLine(mod.limit_modifiers)}`
                      : ""}
                    {availBit(mod)}
                    {mod.included ? null : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          onClick={() =>
                            patch({
                              armor_mods: (ch.armor_mods || []).filter((row) => row.id !== mod.id),
                            })
                          }
                        >
                          外す
                        </button>
                      </>
                    )}
                    {mod.rating_max > 1 && !mod.included ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={mod.rating_max}
                          value={mod.rating}
                          onChange={(e) =>
                            patch({
                              armor_mods: (ch.armor_mods || []).map((row) =>
                                row.id === mod.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                    {mod.has_wireless ? (
                      <label title="ワイヤレス機能を有効化してボーナスを反映">
                        {" "}
                        <input
                          type="checkbox"
                          checked={mod.wireless ?? true}
                          onChange={(e) =>
                            patch({
                              armor_mods: (ch.armor_mods || []).map((row) =>
                                row.id === mod.id ? { ...row, wireless: e.target.checked } : row,
                              ),
                            })
                          }
                        />
                        WL
                      </label>
                    ) : null}
                  </div>
                ))}
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt="改造を追加"
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
                aria-label={`${tr(item.name)} を削除`}
                onClick={() =>
                  patch({
                    armor: (ch.armor || []).filter((row) => row.id !== item.id),
                    armor_mods: (ch.armor_mods || []).filter((row) => row.parent_id !== item.id),
                  })
                }
              >
                削除
              </button>
            </div>
          );
        })}
      </>

      <CatalogPicker
        items={catalog.armor || []}
        label="防具を検索"
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / 装甲 {item.armor} / {item.cost}¥ / {item.avail || "-"} / {item.source}
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
