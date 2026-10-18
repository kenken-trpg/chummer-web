"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { sourceBit } from "@/lib/character/format";

/** The adept's Enhancements: the ones taken, and a searchable list of the
 *  rest. */
export function EnhancementsSection({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch">) {
  const [enhSearch, setEnhSearch] = useState("");
  return (
    <>
      <h3>Enhancement</h3>
      <p className="muted">{ui("adept.enhancementNote")}</p>
      {(d.enhancements || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name}
              {item.power ? ` / ${item.power}` : ""}
              {ui("adept.enhancementCost")}
              {sourceBit(item, ui)}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                adept_enhancements: (ch.adept_enhancements || []).filter((id) => id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("adept.searchEnhancements")}
        aria-label={ui("adept.searchEnhancements")}
        value={enhSearch}
        onChange={(e) => setEnhSearch(e.target.value)}
      />
      <div className="quality-list">
        {(catalog.enhancements || [])
          .filter((item) => {
            const q = enhSearch.trim().toLowerCase();
            return (
              !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
            );
          })
          .filter((item) => !(ch.adept_enhancements || []).includes(item.id))
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name}
                  {item.power ? ` / ${item.power}` : ""}
                  {item.required?.quality?.length ? ` / ${item.required.quality.join(" ・ ")}` : ""}
                  {ui("adept.enhancementCost")}
                  {sourceBit(item, ui)}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    adept_enhancements: [...(ch.adept_enhancements || []), item.id],
                  })
                }
              >
                {ui("common.add")}
              </button>
            </div>
          ))}
      </div>
    </>
  );
}
