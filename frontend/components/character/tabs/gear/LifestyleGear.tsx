"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { CORE_LIFESTYLES } from "@/lib/character/constants";
import { lifeIncrement } from "@/lib/character/format";

export function LifestyleGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.lifestyles || []).map((item) => {
          const raw = (ch.lifestyles || []).find((row) => row.id === item.id);
          const qualityPickKey = `lsq-${item.id}`;
          const ownedUser = new Set(raw?.quality_ids || []);
          const availableQualities = (catalog.lifestyle_qualities || []).filter((q) => {
            if (!q.allow_multiple && ownedUser.has(q.id)) return false;
            if (q.allowed?.length && !q.allowed.includes(item.name)) return false;
            return true;
          });
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / 基本 {(item.base_monthly ?? item.monthly).toLocaleString()}¥
                  {(item.multiplier_pct || 0) !== 0
                    ? ` / 倍率 ${item.multiplier_pct! > 0 ? "+" : ""}${item.multiplier_pct}%`
                    : ""}
                  {(item.quality_monthly || 0) > 0
                    ? ` / 品質 +${item.quality_monthly!.toLocaleString()}¥`
                    : ""}
                  {" / "}
                  {item.monthly.toLocaleString()}¥/{lifeIncrement(item.increment)} × {item.months} ={" "}
                  {item.nuyen.toLocaleString()}¥
                  {item.lp_max ? ` / LP ${item.lp_used || 0}/${item.lp_max}` : ""}
                  {" / "}
                  {item.source}
                </div>
                <div className="cyber-controls">
                  <label>
                    {lifeIncrement(item.increment)}
                    <input
                      type="number"
                      min={1}
                      value={item.months}
                      onChange={(e) =>
                        patch({
                          lifestyles: (ch.lifestyles || []).map((row) =>
                            row.id === item.id ? { ...row, months: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
                {(item.qualities || []).map((q) => (
                  <div className="muted" key={q.id} style={{ marginTop: 6 }}>
                    {tr(q.name)}
                    {q.extra ? `（${q.extra}）` : ""}
                    {q.lp ? ` / LP ${q.lp}` : ""}
                    {q.free ? " / 無料" : q.cost ? ` / +${q.cost.toLocaleString()}¥` : ""}
                    {(q.multiplier || 0) !== 0
                      ? ` / ${q.multiplier! > 0 ? "+" : ""}${q.multiplier}%`
                      : ""}
                    {q.from_freegrid ? (
                      " / 付属"
                    ) : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          onClick={() => {
                            const ids = [...(raw?.quality_ids || [])];
                            const idx = ids.indexOf(q.quality_id);
                            if (idx >= 0) ids.splice(idx, 1);
                            const extras = { ...(raw?.quality_extras || {}) };
                            if (!ids.includes(q.quality_id)) delete extras[q.quality_id];
                            patch({
                              lifestyles: (ch.lifestyles || []).map((row) =>
                                row.id === item.id
                                  ? { ...row, quality_ids: ids, quality_extras: extras }
                                  : row,
                              ),
                            });
                          }}
                        >
                          外す
                        </button>
                      </>
                    )}
                    {q.needs_extra && !q.from_freegrid ? (
                      <input
                        style={{ marginLeft: 8 }}
                        placeholder="対象"
                        value={raw?.quality_extras?.[q.quality_id] || q.extra || ""}
                        onChange={(e) =>
                          patch({
                            lifestyles: (ch.lifestyles || []).map((row) =>
                              row.id === item.id
                                ? {
                                    ...row,
                                    quality_extras: {
                                      ...(row.quality_extras || {}),
                                      [q.quality_id]: e.target.value,
                                    },
                                  }
                                : row,
                            ),
                          })
                        }
                      />
                    ) : null}
                  </div>
                ))}
                {availableQualities.length ? (
                  <div className="cyber-controls">
                    <select
                      value={slotPick[qualityPickKey] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [qualityPickKey]: e.target.value }))
                      }
                    >
                      <option value="">ライフスタイル品質</option>
                      {availableQualities
                        .filter((q) => {
                          const s = gearSearch.trim().toLowerCase();
                          if (!s)
                            return q.source === "SR5" || q.source === "RF" || (q.lp || 0) !== 0;
                          return (
                            q.name.toLowerCase().includes(s) || tr(q.name).toLowerCase().includes(s)
                          );
                        })
                        .slice(0, 80)
                        .map((q) => (
                          <option key={q.id} value={q.id}>
                            {tr(q.name)} (LP {q.lp}
                            {q.cost ? ` / ${q.cost}¥` : ""}
                            {q.multiplier ? ` / ${q.multiplier}%` : ""})
                          </option>
                        ))}
                    </select>
                    {(() => {
                      const qspec = availableQualities.find(
                        (q) => q.id === slotPick[qualityPickKey],
                      );
                      if (!qspec?.needs_extra) return null;
                      return (
                        <input
                          placeholder="対象"
                          value={extraPick[qualityPickKey] || ""}
                          onChange={(e) =>
                            setExtraPick((cur) => ({ ...cur, [qualityPickKey]: e.target.value }))
                          }
                        />
                      );
                    })()}
                    <button
                      className="btn"
                      disabled={!slotPick[qualityPickKey]}
                      onClick={() => {
                        const qid = slotPick[qualityPickKey];
                        if (!qid) return;
                        const extras = { ...(raw?.quality_extras || {}) };
                        if (extraPick[qualityPickKey]) extras[qid] = extraPick[qualityPickKey];
                        patch({
                          lifestyles: (ch.lifestyles || []).map((row) =>
                            row.id === item.id
                              ? {
                                  ...row,
                                  quality_ids: [...(row.quality_ids || []), qid],
                                  quality_extras: extras,
                                }
                              : row,
                          ),
                        });
                        setSlotPick((cur) => ({ ...cur, [qualityPickKey]: "" }));
                        setExtraPick((cur) => ({ ...cur, [qualityPickKey]: "" }));
                      }}
                    >
                      追加
                    </button>
                  </div>
                ) : null}
              </div>
              <button
                className="btn danger"
                onClick={() =>
                  patch({
                    lifestyles: (ch.lifestyles || []).filter((row) => row.id !== item.id),
                  })
                }
              >
                削除
              </button>
            </div>
          );
        })}
      </>

      <input
        type="search"
        placeholder="ライフスタイルを検索"
        aria-label="ライフスタイルを検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />
      <div className="quality-list">
        {(catalog.lifestyles || [])
          .filter((item) => {
            const q = gearSearch.trim().toLowerCase();
            if (q)
              return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
            return CORE_LIFESTYLES.has(item.name);
          })
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {item.cost.toLocaleString()}¥/{lifeIncrement(item.increment)}
                  {item.lp ? ` / LP ${item.lp}` : ""}
                  {(item.freegrids || []).length ? ` / 付属グリッド ${item.freegrids!.length}` : ""}
                  {" / "}
                  {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    lifestyles: [
                      ...(ch.lifestyles || []),
                      { lifestyle_id: item.id, months: 1, quality_ids: [] },
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
