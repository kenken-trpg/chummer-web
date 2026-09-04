"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { CORE_LIFESTYLES } from "@/lib/character/constants";
import { lifeIncrement } from "@/lib/character/format";

export function LifestyleGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      <>
        {(d.lifestyles || []).map((item) => {
          const raw = (ch.lifestyles || []).find((row) => row.id === item.id);
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
                  {item.name} /{" "}
                  {ui("life.base", {
                    cost: (item.base_monthly ?? item.monthly).toLocaleString(),
                  })}
                  {(item.multiplier_pct || 0) !== 0
                    ? ui("life.multiplier", {
                        pct: `${item.multiplier_pct! > 0 ? "+" : ""}${item.multiplier_pct}`,
                      })
                    : ""}
                  {(item.quality_monthly || 0) > 0
                    ? ui("life.qualityCost", { cost: item.quality_monthly!.toLocaleString() })
                    : ""}
                  {" / "}
                  {item.monthly.toLocaleString()}¥/{lifeIncrement(item.increment, ui)} ×{" "}
                  {item.months} = {item.nuyen.toLocaleString()}¥
                  {item.lp_max
                    ? ui("life.lpUsed", { used: item.lp_used || 0, max: item.lp_max })
                    : ""}
                  {" / "}
                  {item.source}
                </div>
                <div className="cyber-controls">
                  <label>
                    {lifeIncrement(item.increment, ui)}
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
                    {q.lp ? ui("life.lp", { lp: q.lp }) : ""}
                    {q.free
                      ? ui("common.freeSlot")
                      : q.cost
                        ? ` / +${q.cost.toLocaleString()}¥`
                        : ""}
                    {(q.multiplier || 0) !== 0
                      ? ` / ${q.multiplier! > 0 ? "+" : ""}${q.multiplier}%`
                      : ""}
                    {q.from_freegrid ? (
                      ` / ${ui("common.included")}`
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
                          {ui("common.remove")}
                        </button>
                      </>
                    )}
                    {q.needs_extra && !q.from_freegrid ? (
                      <input
                        style={{ marginLeft: 8 }}
                        placeholder={ui("common.target")}
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
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt={ui("life.quality")}
                  addLabel={ui("common.add")}
                  tr={tr}
                  // the SR5/RF-or-costed narrowing used to lift as soon as the
                  // catalog search box below had text in it; it is unrelated
                  // to this control, so it now always applies
                  options={availableQualities.filter(
                    (q) => q.source === "SR5" || q.source === "RF" || (q.lp || 0) !== 0,
                  )}
                  optionLabel={(q) =>
                    `${tr(q.name)} (LP ${q.lp}${q.cost ? ` / ${q.cost}¥` : ""}${
                      q.multiplier ? ` / ${q.multiplier}%` : ""
                    })`
                  }
                  extraFor={(q) =>
                    q.needs_extra
                      ? { label: ui("common.target"), values: [], freeText: true }
                      : null
                  }
                  onAdd={(q, extra) => {
                    const extras = { ...(raw?.quality_extras || {}) };
                    if (extra) extras[q.id] = extra;
                    patch({
                      lifestyles: (ch.lifestyles || []).map((row) =>
                        row.id === item.id
                          ? {
                              ...row,
                              quality_ids: [...(row.quality_ids || []), q.id],
                              quality_extras: extras,
                            }
                          : row,
                      ),
                    });
                  }}
                />
              </div>
              <button
                className="btn danger"
                onClick={() =>
                  patch({
                    lifestyles: (ch.lifestyles || []).filter((row) => row.id !== item.id),
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
        items={catalog.lifestyles || []}
        label={ui("gear.searchLifestyle")}
        tr={tr}
        idle={{
          keep: (item) => CORE_LIFESTYLES.has(item.name),
          note: "gear.idleLifestyles",
        }}
        describe={(item) => (
          <>
            {item.name} / {item.cost.toLocaleString()}¥/{lifeIncrement(item.increment, ui)}
            {item.lp ? ui("life.lp", { lp: item.lp }) : ""}
            {(item.freegrids || []).length
              ? ui("life.freeGrids", { count: item.freegrids!.length })
              : ""}
            {" / "}
            {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            lifestyles: [
              ...(ch.lifestyles || []),
              { lifestyle_id: item.id, months: 1, quality_ids: [] },
            ],
          })
        }
      />
    </>
  );
}
