"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { optionalNumber, testLine } from "@/lib/character/format";

export function FociTab({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [focusSearch, setFocusSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        購入は定価。クラフトは術式＋試薬Force×20¥とアーティフィシング+MAG[Force] vs
        Force×2（Force日）。結合カルマは Force。同時 {d.focus_limits?.count || 0}/
        {d.focus_limits?.count_max || 0} ・ Force合計 {d.focus_limits?.force || 0}/
        {d.focus_limits?.force_max || 0}
        {d.enabled_tabs.includes("adept") ? " ・ 気焦点はアデプトタブ（この上限に含む）" : ""}
      </p>
      {(d.foci || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name} / F{item.force} / {item.crafted ? "クラフト" : "購入"} /{" "}
              {item.nuyen.toLocaleString()}¥ / 結合 {item.karma}カルマ
              {item.crafted
                ? `（術式 ${item.formula_nuyen?.toLocaleString() || 0}¥ + 試薬 ${item.reagent_nuyen?.toLocaleString() || 0}¥ / 定価 ${item.retail_nuyen?.toLocaleString() || 0}¥）`
                : ""}
              {item.effect ? ` / ${item.effect.replace(/Rating/g, String(item.force))}` : ""}
              {item.needs_weapon
                ? item.weapon_name
                  ? ` / 対象 ${tr(item.weapon_name)} +${item.weapon_dice || item.force}`
                  : " / 対象武器が必要"
                : ""}
              {" / "}
              {item.source}
            </div>
            {item.formula_test ? (
              <div className="muted">術式自作 {testLine(item.formula_test)}</div>
            ) : null}
            {item.test ? <div className="muted">{testLine(item.test)}</div> : null}
            <div className="cyber-controls">
              <label>
                Force
                <input
                  type="number"
                  min={1}
                  max={item.force_max}
                  value={item.force}
                  onChange={(e) =>
                    patch({
                      foci: (ch.foci || []).map((row) =>
                        row.id === item.id ? { ...row, force: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              {item.needs_weapon ? (
                <label>
                  対象武器
                  <select
                    value={item.weapon_id || ""}
                    onChange={(e) =>
                      patch({
                        foci: (ch.foci || []).map((row) =>
                          row.id === item.id ? { ...row, extra: e.target.value || null } : row,
                        ),
                      })
                    }
                  >
                    <option value="">{item.weapon_type === "Melee" ? "近接武器" : "武器"}</option>
                    {(item.weapon_options || []).map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {tr(opt.name)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              {item.crafted ? (
                <>
                  <label>
                    作成ヒット
                    <input
                      type="number"
                      min={0}
                      value={item.hits ?? ""}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, hits: optionalNumber(e.target.value) }
                              : row,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    抵抗ヒット
                    <input
                      type="number"
                      min={0}
                      value={item.opposed_hits ?? ""}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, opposed_hits: optionalNumber(e.target.value) }
                              : row,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    術式
                    <select
                      value={item.formula_bought ? "buy" : "design"}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, formula_bought: e.target.value === "buy" }
                              : row,
                          ),
                        })
                      }
                    >
                      <option value="buy">購入</option>
                      <option value="design">自作（アーカナ）</option>
                    </select>
                  </label>
                </>
              ) : null}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                foci: (ch.foci || []).filter((row) => row.id !== item.id),
              })
            }
          >
            削除
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder="フォーカスを検索"
        aria-label="フォーカスを検索"
        value={focusSearch}
        onChange={(e) => setFocusSearch(e.target.value)}
      />
      <div className="quality-list">
        {(catalog.foci || [])
          .filter((item) => {
            const q = focusSearch.trim().toLowerCase();
            if (q) {
              return (
                item.name.toLowerCase().includes(q) ||
                tr(item.name).toLowerCase().includes(q) ||
                (item.effect || "").toLowerCase().includes(q)
              );
            }
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / 購入 {item.cost}
                  {item.formula ? ` / クラフト 術式 ${item.formula.cost} + 試薬 20¥×F` : ""}
                  {" / "}
                  {item.effect || "結合のみ"}
                  {item.needs_weapon ? ` / ${item.weapon_type || "Melee"}武器指定` : ""}
                  {" / "}
                  {item.source}
                </div>
              </div>
              <div>
                <button
                  className="btn"
                  onClick={() =>
                    patch({
                      foci: [...(ch.foci || []), { gear_id: item.id, force: 1, crafted: false }],
                    })
                  }
                >
                  購入
                </button>{" "}
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      foci: [
                        ...(ch.foci || []),
                        { gear_id: item.id, force: 1, crafted: true, formula_bought: true },
                      ],
                    })
                  }
                >
                  クラフト
                </button>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
