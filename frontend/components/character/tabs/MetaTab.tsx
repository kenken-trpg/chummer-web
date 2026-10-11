"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { talentLabel } from "@/lib/character/talent-labels";
import { withOriginal } from "@/lib/character/format";
import { priorityTableFor } from "@/lib/character/priority-table";
import { critterPowerRow } from "@/lib/spell-terms";

export function MetaTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const table = priorityTableFor(catalog, ch.settings?.priority_table);
  const candidates =
    (ch.build_method || "Priority") === "Karma"
      ? catalog.metatypes.map((m) => ({ name: m.name, special: 0, karma: m.karma ?? 0 }))
      : table.Heritage[ch.priorities.Heritage].metatypes;

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("help.meta.statsLabel") })}
          lines={[
            { label: ui("help.meta.special") },
            { label: ui("help.meta.karma") },
            { label: ui("help.meta.variant") },
            { label: ui("help.meta.talent") },
          ]}
        >
          {ui("help.meta.statsLabel")}
        </HelpTip>
      </p>
      {!candidates.some((m) => m.name === ch.metatype) ? (
        <p role="status" className="muted">
          {ui("meta.retained", { name: tr(ch.metatype) })}
          {d.metatype_info.source ? ` / ${d.metatype_info.source}` : ""}
        </p>
      ) : null}
      <div className="grid">
        {candidates.map((m) => (
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
      {d.metatype_info.powers?.length ? (
        <section style={{ marginTop: 12 }}>
          <h3>{ui("meta.innatePowers")}</h3>
          <p className="muted">{ui("meta.innate", { name: tr(ch.metatype) })}</p>
          <ul className="critter-powers">
            {d.metatype_info.powers.map((power, index) => (
              <li key={`${power.id}-${index}`}>
                {critterPowerRow(power, tr, ui)}
                <span className="muted">
                  {" "}
                  / {power.source} p.{power.page}
                </span>
                {power.select ? <div className="muted">{power.select}</div> : null}
                {power.rating ? <div className="muted">{power.rating}</div> : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
