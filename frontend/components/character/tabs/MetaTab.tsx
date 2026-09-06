"use client";
import type { TabPanelProps } from "@/components/character/types";
import { talentLabel } from "@/lib/character/talent-labels";
import { withOriginal } from "@/lib/character/format";

export function MetaTab({ catalog, character: ch, tr, ui, patch }: TabPanelProps) {
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
                ? ui("common.karmaCost", {
                    karma: ("karma" in m ? Number(m.karma) : 0) || 0,
                  })
                : ui("meta.special", { points: m.special })}
            </div>
          </button>
        ))}
      </div>
      {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants?.length ? (
        <div style={{ marginTop: 12 }}>
          <label className="muted stacked-label">
            {ui("meta.metavariant")}
            <select
              value={ch.metavariant || ""}
              onChange={(e) => patch({ metavariant: e.target.value || null })}
            >
              <option value="">{ui("meta.noVariant", { name: tr(ch.metatype) })}</option>
              {catalog.metatypes
                .find((m) => m.name === ch.metatype)
                ?.metavariants.map((v) => (
                  <option key={v.name} value={v.name}>
                    {withOriginal(v.name, tr)}
                  </option>
                ))}
            </select>
          </label>
        </div>
      ) : null}
      <div style={{ marginTop: 12 }}>
        <label className="muted stacked-label">
          {ui("prio.talent")}
          <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
            {((ch.build_method || "Priority") === "Karma"
              ? (catalog.karma_talents || []).map((t) => ({
                  name: t.name,
                  label: t.label || t.name,
                }))
              : table.Talent[ch.priorities.Talent].talents
            ).map((t) => (
              <option key={t.name} value={t.name}>
                {talentLabel(t.name, t.label, ui)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
