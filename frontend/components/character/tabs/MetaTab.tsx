"use client";

import type { TabPanelProps } from "@/components/character/types";

export function MetaTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const table = catalog.priority_table;

  return (
    <div className="card">
      <div className="grid">
        {((ch.build_method || "Priority") === "Karma"
          ? catalog.metatypes.map((m) => ({
              name: m.name,
              special: 0,
              karma: m.karma ?? 0,
            }))
          : table.Heritage[ch.priorities.Heritage].metatypes
        ).map((m) => (
          <button
            key={m.name}
            className={`choice ${ch.metatype === m.name ? "selected" : ""}`}
            onClick={() => patch({ metatype: m.name, metavariant: null })}
          >
            <b>{tr(m.name)}</b>
            <div className="muted">
              {m.name}
              {(ch.build_method || "Priority") === "Karma"
                ? ` / ${("karma" in m ? Number(m.karma) : 0) || 0}カルマ`
                : ` / 特殊点 ${m.special}`}
            </div>
          </button>
        ))}
      </div>
      {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants?.length ? (
        <div style={{ marginTop: 12 }}>
          <label className="muted">メタバリアント</label>
          <select
            value={ch.metavariant || ""}
            onChange={(e) => patch({ metavariant: e.target.value || null })}
          >
            <option value="">なし（{tr(ch.metatype)}）</option>
            {catalog.metatypes
              .find((m) => m.name === ch.metatype)
              ?.metavariants.map((v) => (
                <option key={v.name} value={v.name}>
                  {tr(v.name)} ({v.name})
                </option>
              ))}
          </select>
        </div>
      ) : null}
      <div style={{ marginTop: 12 }}>
        <label className="muted">タレント</label>
        <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
          {((ch.build_method || "Priority") === "Karma"
            ? (catalog.karma_talents || []).map((t) => ({ name: t.name, label: t.label || t.name }))
            : table.Talent[ch.priorities.Talent].talents
          ).map((t) => (
            <option key={t.name} value={t.name}>
              {t.label || t.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
