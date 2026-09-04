"use client";
import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { cfDuration, cfTarget, testLine } from "@/lib/character/format";

export function ComplexFormsTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [cfSearch, setCfSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        {ui("cf.free", {
          used: d.complex_form_points?.used || 0,
          free: d.complex_form_points?.free || 0,
        })}
        {(d.complex_form_points?.paid || 0) > 0
          ? ui("cf.paid", { paid: d.complex_form_points?.paid || 0 })
          : ""}
        {d.fade_resist
          ? ui("res.fadeResist", { attrs: d.fade_resist.attrs, pool: d.fade_resist.pool })
          : ""}
        {ui("cf.note")}
      </p>
      {(d.complex_forms || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.label || item.name)}</b>
            <div className="muted">
              {item.name} / {cfTarget(item.target, ui)} / {cfDuration(item.duration, ui)} /{" "}
              {item.fv}
              {ui("cf.fadeAt", {
                level: item.level,
                fade:
                  item.fade == null ? ui("cf.fadeSpecial") : `${item.fade}${item.fade_code || ""}`,
              })}
              {item.free ? ui("common.freeSlot") : ui("common.karmaCost", { karma: item.karma })}
              {" / "}
              {item.source}
            </div>
            {item.test ? <div className="muted">{testLine(item.test, ui, "fmt.fade")}</div> : null}
            <div className="cyber-controls">
              <label>
                Level
                <input
                  type="number"
                  min={item.level_min}
                  max={item.level_max}
                  value={item.level}
                  onChange={(e) =>
                    patch({
                      complex_forms: (ch.complex_forms || []).map((row) =>
                        row.id === item.id ? { ...row, level: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              {item.needs_extra ? (
                <label>
                  {ui("cf.attribute")}
                  <select
                    value={item.extra || ""}
                    onChange={(e) =>
                      patch({
                        complex_forms: (ch.complex_forms || []).map((row) =>
                          row.id === item.id ? { ...row, extra: e.target.value } : row,
                        ),
                      })
                    }
                  >
                    <option value="">{ui("common.choose")}</option>
                    {(item.options || []).map((name) => (
                      <option key={name} value={name}>
                        {tr(name)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                complex_forms: (ch.complex_forms || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("cf.search")}
        aria-label={ui("cf.search")}
        value={cfSearch}
        onChange={(e) => setCfSearch(e.target.value)}
      />
      <div className="quality-list">
        <PickerList
          items={(catalog.complex_forms || [])
            .filter((item) => !(ch.complex_forms || []).some((row) => row.form_id === item.id))
            .filter((item) => {
              const q = cfSearch.trim().toLowerCase();
              if (q) {
                return (
                  item.name.toLowerCase().includes(q) ||
                  tr(item.name).toLowerCase().includes(q) ||
                  (item.target || "").toLowerCase().includes(q)
                );
              }
              return item.source === "SR5";
            })}
          note={cfSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => {
            const paid = (d.complex_form_points?.used || 0) >= (d.complex_form_points?.free || 0);
            const blocked = (item.required || []).length
              ? ui("cf.required", {
                  list: item.required!.map((name) => tr(name)).join(ui("common.termSep")),
                })
              : "";
            return (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {cfTarget(item.target, ui)} / {cfDuration(item.duration, ui)} /{" "}
                    {item.fv} / {item.source}
                    {item.needs_extra ? ui("cf.needsAttr") : ""}
                    {blocked ? ` / ${blocked}` : ""}
                    {paid ? ui("common.karmaCost", { karma: 4 }) : ui("common.freeSlot")}
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      complex_forms: [...(ch.complex_forms || []), { form_id: item.id }],
                    })
                  }
                >
                  {ui("common.add")}
                </button>
              </div>
            );
          }}
        </PickerList>
      </div>
    </div>
  );
}
