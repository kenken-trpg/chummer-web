"use client";
import { useState } from "react";
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
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});

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
                {addons.length ? (
                  <div className="cyber-controls">
                    <select
                      value={slotPick[item.id] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                      }
                    >
                      <option value="">改造を追加</option>
                      {addons
                        .filter((mod) => gearSearch.trim() || mod.source === "SR5")
                        .map((mod) => (
                          <option key={mod.id} value={mod.id}>
                            {tr(mod.name)} ({formatAccessoryCost(mod.cost, parentCost)})
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
                          armor_mods: [
                            ...(ch.armor_mods || []),
                            {
                              mod_id: spec.id,
                              parent_id: item.id,
                              rating: Math.max(1, spec.minrating || 1),
                            },
                          ],
                        });
                        setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                      }}
                    >
                      装着
                    </button>
                  </div>
                ) : null}
              </div>
              <button
                className="btn danger"
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

      <div className="option-row">
        <button
          className={`tab ${gearCat === "all" ? "active" : ""}`}
          onClick={() => setGearCat("all")}
        >
          すべて
        </button>
        {[...new Set((catalog.armor || []).map((item) => item.category))].sort().map((cat) => (
          <button
            key={cat}
            className={`tab ${gearCat === cat ? "active" : ""}`}
            onClick={() => setGearCat(cat)}
          >
            {tr(cat)}
          </button>
        ))}
      </div>
      <input
        type="search"
        placeholder="防具を検索"
        aria-label="防具を検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
        {(catalog.armor || [])
          .filter((item) => gearCat === "all" || item.category === gearCat)
          .filter((item) => {
            const q = gearSearch.trim().toLowerCase();
            if (q)
              return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / 装甲 {item.armor} / {item.cost}¥ / {item.avail || "-"} /{" "}
                  {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    armor: [
                      ...(ch.armor || []),
                      {
                        armor_id: item.id,
                        rating: Math.max(1, item.minrating || 1),
                        equipped: true,
                      },
                    ],
                  })
                }
              >
                購入
              </button>
            </div>
          ))}
      </div>
    </>
  );
}
