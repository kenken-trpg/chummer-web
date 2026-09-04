"use client";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";

export function MartialTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [martialSearch, setMartialSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        {ui("martial.styles", {
          styles: d.martial_art_points?.styles || 0,
          max: d.martial_art_points?.style_max || 1,
        })}
        {ui("martial.techniques", {
          used: d.martial_art_points?.techniques || 0,
          max: d.martial_art_points?.technique_max || 5,
        })}
        {ui("martial.karma", { karma: d.martial_art_points?.karma || 0 })}
        {ui("martial.note")}
        {(d.unarmed_reach || 0) > 0
          ? ui("martial.unarmedReach", { reach: d.unarmed_reach || 0 })
          : ""}
      </p>
      {(d.martial_arts || []).map((item) => {
        const local = (ch.martial_arts || []).find((row) => row.id === item.id);
        const selected = new Set(local?.techniques || item.techniques.map((tech) => tech.name));
        const techMax = item.technique_max ?? null;
        return (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name}
                {item.free
                  ? ui("martial.freeQuality")
                  : ui("martial.cost", { karma: item.karma, style: item.style_karma })}
                {" / "}
                {item.source}
                {item.page ? ` p.${item.page}` : ""}
                {techMax === 1 ? ui("martial.oneTech") : ""}
              </div>
              <div className="martial-techs" style={{ display: "grid", gap: 4, marginTop: 8 }}>
                {item.technique_options.map((name) => {
                  const owned = selected.has(name);
                  const techMeta = item.techniques.find((tech) => tech.name === name);
                  const atCap = techMax != null && !owned && selected.size >= techMax;
                  return (
                    <label key={name} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <input
                        type="checkbox"
                        checked={owned}
                        disabled={atCap}
                        onChange={(e) => {
                          const next = new Set(selected);
                          if (e.target.checked) {
                            if (techMax === 1) next.clear();
                            next.add(name);
                          } else {
                            next.delete(name);
                          }
                          const techniques = item.technique_options.filter((opt) => next.has(opt));
                          patch({
                            martial_arts: (ch.martial_arts || []).map((row) =>
                              row.id === item.id ? { ...row, techniques } : row,
                            ),
                          });
                        }}
                      />
                      <span>
                        {tr(name)}
                        {owned && techMeta?.free
                          ? ui("martial.techIncluded")
                          : owned
                            ? ui("common.karmaCost", { karma: techMeta?.karma || 5 })
                            : ""}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
            {item.locked ? (
              <span className="muted">{ui("common.fromQuality")}</span>
            ) : (
              <button
                className="btn"
                onClick={() =>
                  patch({
                    martial_arts: (ch.martial_arts || []).filter((row) => row.id !== item.id),
                  })
                }
              >
                {ui("common.delete")}
              </button>
            )}
          </div>
        );
      })}
      <input
        type="search"
        placeholder={ui("martial.search")}
        aria-label={ui("martial.search")}
        value={martialSearch}
        onChange={(e) => setMartialSearch(e.target.value)}
      />
      <div className="list">
        <PickerList
          items={(catalog.martial_arts || []).filter((item) => {
            const q = martialSearch.trim().toLowerCase();
            if (!q) return true;
            return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
          })}
        >
          {(item) => {
            const owned = (d.martial_arts || []).some((row) => row.art_id === item.id);
            const blocked =
              !owned &&
              (d.martial_art_points?.styles || 0) >= (d.martial_art_points?.style_max || 1);
            return (
              <div className="list-row" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {ui("martial.rowCost", { karma: item.cost })} /{" "}
                    {ui("martial.techCount", { count: item.techniques.length })} / {item.source}
                    {item.spec_options?.length
                      ? ui("martial.specOptions", {
                          list: item.spec_options
                            .map((opt) => `${opt.skill}:${opt.spec}`)
                            .join(", "),
                        })
                      : ""}
                  </div>
                </div>
                <button
                  className="btn"
                  disabled={owned || blocked}
                  onClick={() => {
                    const first = item.techniques[0];
                    if (!first) return;
                    patch({
                      martial_arts: [
                        ...(ch.martial_arts || []),
                        { art_id: item.id, techniques: [first] },
                      ],
                    });
                  }}
                >
                  {owned
                    ? ui("martial.owned")
                    : blocked
                      ? ui("martial.capped")
                      : ui("martial.take")}
                </button>
              </div>
            );
          }}
        </PickerList>
      </div>
    </div>
  );
}
