"use client";
import type { TabPanelProps } from "@/components/character/types";
import { spiritRoleLabel } from "@/lib/character/constants";
import { optionalNumber, testLine } from "@/lib/character/format";

export function SpiritsTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <div className="card">
      <p className="muted">
        {ui("spirit.note")}
        {d.drain_resist
          ? ui("magic.drainResist", { attrs: d.drain_resist.attrs, pool: d.drain_resist.pool })
          : ""}
        {(d.limit_spirit_categories || []).length
          ? ui("spirit.allowed", {
              list: (d.limit_spirit_categories || []).join(ui("common.listSep")),
            })
          : ""}
        {(d.extra_spirits || []).length
          ? ui("spirit.extra", { list: (d.extra_spirits || []).join(ui("common.listSep")) })
          : ""}
      </p>
      <label>
        {ui("magic.tradition")}
        <select
          value={ch.tradition_id || ""}
          onChange={(e) => patch({ tradition_id: e.target.value || null })}
        >
          <option value="">{ui("common.choose")}</option>
          {(catalog.traditions || []).map((item) => (
            <option key={item.id} value={item.id}>
              {tr(item.name)}（{item.drain_attrs.join("+")}）
            </option>
          ))}
        </select>
      </label>
      {(d.spirits || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name} / {item.role_label || item.role} /{" "}
              {item.bound ? ui("spirit.bound") : ui("spirit.summoned")} / F{item.force} /{" "}
              {ui("spirit.services")} {item.services}
              {item.bound
                ? ui("spirit.reagent", { nuyen: item.nuyen.toLocaleString() })
                : ui("spirit.untilDawn")}
              {" / "}
              {item.source}
            </div>
            {item.test ? <div className="muted">{testLine(item.test, ui)}</div> : null}
            {item.attributes ? (
              <div className="muted">
                {["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA"]
                  .map((key) => `${key} ${item.attributes?.[key] ?? "-"}`)
                  .join(" ・ ")}
                {item.attributes.INI != null ? ` ・ INI ${item.attributes.INI}` : ""}
              </div>
            ) : null}
            {item.powers?.length ? (
              <div className="muted">
                {ui("common.powers", {
                  list: item.powers.map((name) => tr(name)).join(ui("common.termSep")),
                })}
              </div>
            ) : null}
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
                      spirits: (ch.spirits || []).map((row) =>
                        row.id === item.id ? { ...row, force: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                {ui("spirit.services")}
                <input
                  type="number"
                  min={0}
                  max={item.force_max}
                  value={item.services}
                  onChange={(e) =>
                    patch({
                      spirits: (ch.spirits || []).map((row) =>
                        row.id === item.id
                          ? {
                              ...row,
                              services: Number(e.target.value),
                              hits: null,
                              opposed_hits: null,
                            }
                          : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                {ui("common.hits", {
                  kind: item.bound ? ui("spirit.bind") : ui("spirit.summon"),
                })}
                <input
                  type="number"
                  min={0}
                  value={item.hits ?? ""}
                  onChange={(e) =>
                    patch({
                      spirits: (ch.spirits || []).map((row) =>
                        row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                {ui("spirit.spiritHits")}
                <input
                  type="number"
                  min={0}
                  value={item.opposed_hits ?? ""}
                  onChange={(e) =>
                    patch({
                      spirits: (ch.spirits || []).map((row) =>
                        row.id === item.id
                          ? { ...row, opposed_hits: optionalNumber(e.target.value) }
                          : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                {ui("common.kind")}
                <select
                  value={item.bound ? "bound" : "summoned"}
                  onChange={(e) =>
                    patch({
                      spirits: (ch.spirits || []).map((row) =>
                        row.id === item.id ? { ...row, bound: e.target.value === "bound" } : row,
                      ),
                    })
                  }
                >
                  <option value="summoned">{ui("spirit.summoned")}</option>
                  <option value="bound">{ui("spirit.bound")}</option>
                </select>
              </label>
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                spirits: (ch.spirits || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <div className="quality-list">
        {Object.entries(d.tradition?.spirits || {}).map(([role, name]) => {
          const spec = (catalog.spirits || []).find((row) => row.name === name);
          if (!spec) return null;
          const limits = d.limit_spirit_categories || [];
          if (limits.length && !limits.includes(spec.name)) return null;
          return (
            <div className="quality-item" key={role}>
              <div>
                <b>{tr(spec.name)}</b>
                <div className="muted">
                  {spec.name} / {spiritRoleLabel(role, ui)} / {ui("spirit.tests")} / {spec.source}
                </div>
                <div className="muted">
                  {["BOD", "AGI", "REA", "STR"]
                    .map((key) => `${key} ${spec.attributes?.[key] || "F"}`)
                    .join(` ${ui("common.termSep")} `)}
                </div>
              </div>
              <div>
                <button
                  className="btn"
                  onClick={() =>
                    patch({
                      spirits: [
                        ...(ch.spirits || []),
                        { spirit_id: spec.id, force: 1, services: 1, bound: false },
                      ],
                    })
                  }
                >
                  {ui("spirit.summon")}
                </button>{" "}
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      spirits: [
                        ...(ch.spirits || []),
                        { spirit_id: spec.id, force: 1, services: 1, bound: true },
                      ],
                    })
                  }
                >
                  {ui("spirit.bind")}
                </button>
              </div>
            </div>
          );
        })}
        {(d.extra_spirits || []).map((name) => {
          if (Object.values(d.tradition?.spirits || {}).includes(name)) return null;
          const spec = (catalog.spirits || []).find((row) => row.name === name);
          if (!spec) return null;
          return (
            <div className="quality-item" key={`extra-${name}`}>
              <div>
                <b>{tr(spec.name)}</b>
                <div className="muted">
                  {spec.name} / {ui("spirit.extraTag")} / {ui("spirit.tests")} / {spec.source}
                </div>
              </div>
              <div>
                <button
                  className="btn"
                  onClick={() =>
                    patch({
                      spirits: [
                        ...(ch.spirits || []),
                        { spirit_id: spec.id, force: 1, services: 1, bound: false },
                      ],
                    })
                  }
                >
                  {ui("spirit.summon")}
                </button>{" "}
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      spirits: [
                        ...(ch.spirits || []),
                        { spirit_id: spec.id, force: 1, services: 1, bound: true },
                      ],
                    })
                  }
                >
                  {ui("spirit.bind")}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
