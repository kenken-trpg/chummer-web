"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { renderNotices } from "@/lib/engine-notices";
import type { CustomDrugInstall, DrugComponentCatalogItem } from "@/lib/types";

/** Foundation first: it is the one part a drug must have, and it decides what
 *  the blocks under it are allowed to do (CF p.190). */
const CATEGORY_ORDER = ["Foundation", "Block", "Enhancer"];

function sortComponents(items: DrugComponentCatalogItem[]) {
  return [...items].sort(
    (a, b) =>
      CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category) ||
      a.name.localeCompare(b.name),
  );
}

/**
 * Mixing a drug from components, rather than buying one off the catalog.
 *
 * The drug is patched as it is built rather than assembled in local state and
 * saved at the end: every total on screen — price, availability, addiction,
 * onset, and what it does to the character while it is active — comes back
 * from the engine, and the rules it breaks come back as ordinary creation
 * errors on the checklist.
 */
export function CustomDrugMixer({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [pick, setPick] = useState<Record<string, string>>({});
  const components = catalog.drug_components || [];
  const grades = catalog.drug_component_grades || [];
  const owned = ch.custom_drugs || [];
  const rows = d.custom_drugs || [];

  const patchDrugs = (next: CustomDrugInstall[]) => patch({ custom_drugs: next });
  // By position, not by id: a drug just mixed has no id until the server hands
  // one back, and two id-less rows would otherwise edit each other.
  const editDrug = (index: number, change: Partial<CustomDrugInstall>) =>
    patchDrugs(owned.map((drug, i) => (i === index ? { ...drug, ...change } : drug)));

  return (
    <div className="cyber-block">
      <h4>{ui("customDrug.title")}</h4>
      <p className="muted">{ui("customDrug.help")}</p>
      {owned.map((drug, index) => {
        const row = rows.find((item) => item.id === drug.id);
        const key = drug.id || `new-${index}`;
        const parts = drug.parts || [];
        const picked = pick[key] || "";
        const spec = components.find((item) => item.id === picked.split("@")[0]);
        return (
          <div className="cyber-item" key={key}>
            <div>
              <input
                aria-label={ui("customDrug.name")}
                placeholder={ui("customDrug.name")}
                value={drug.name || ""}
                onChange={(e) => editDrug(index, { name: e.target.value })}
              />
              <select
                aria-label={ui("customDrug.grade")}
                value={drug.grade || "Standard"}
                onChange={(e) => editDrug(index, { grade: e.target.value })}
              >
                {grades.map((grade) => (
                  <option key={grade.id} value={grade.name}>
                    {tr(grade.name)} (×{grade.cost_multiplier})
                  </option>
                ))}
              </select>
              {row ? (
                <div className="muted">
                  {row.nuyen.toLocaleString()}¥ / {ui("customDrug.avail", { avail: row.avail })} /{" "}
                  {ui("customDrug.addiction", {
                    rating: row.addiction_rating,
                    threshold: row.addiction_threshold,
                  })}
                  {" / "}
                  {ui("customDrug.onset", { seconds: row.speed })}
                  {row.crash_damage
                    ? ` / ${ui("customDrug.crash", { damage: row.crash_damage })}`
                    : ""}
                  {row.duration ? ` / ${ui("customDrug.duration", { seconds: row.duration })}` : ""}
                  {row.infos.length ? ` / ${row.infos.map(tr).join(ui("common.listSep"))}` : ""}
                </div>
              ) : null}
              {row?.effect?.length ? (
                <div className="muted">
                  {ui("gear.effect")}: {renderNotices(row.effect, ui, tr)}
                </div>
              ) : null}
              {parts.map((part, partIndex) => {
                const partSpec = components.find((item) => item.id === part.component_id);
                if (!partSpec) return null;
                return (
                  <div
                    className="muted"
                    key={`${part.component_id}-${partIndex}`}
                    style={{ marginTop: 6 }}
                  >
                    {tr(partSpec.category)} / {tr(partSpec.name)}
                    {partSpec.levels.length > 1
                      ? ` (${ui("customDrug.level", { level: (part.level || 0) + 1 })})`
                      : ""}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        editDrug(index, {
                          parts: parts.filter((_, i) => i !== partIndex),
                        })
                      }
                    >
                      {ui("common.remove")}
                    </button>
                  </div>
                );
              })}
              <div className="cyber-controls">
                <select
                  aria-label={`${drug.name || ui("customDrug.name")}: ${ui("customDrug.addComponent")}`}
                  value={picked}
                  onChange={(e) => setPick((cur) => ({ ...cur, [key]: e.target.value }))}
                >
                  <option value="">{ui("customDrug.addComponent")}</option>
                  {sortComponents(components).map((item) =>
                    item.levels.map((level) => (
                      <option key={`${item.id}@${level.level}`} value={`${item.id}@${level.level}`}>
                        {tr(item.category)} / {tr(item.name)}
                        {item.levels.length > 1
                          ? ` (${ui("customDrug.level", { level: level.level + 1 })})`
                          : ""}{" "}
                        — {renderNotices(level.effect, ui, tr)}
                      </option>
                    )),
                  )}
                </select>
                <button
                  className="btn"
                  disabled={!spec}
                  onClick={() => {
                    if (!spec) return;
                    editDrug(index, {
                      parts: [
                        ...parts,
                        { component_id: spec.id, level: Number(picked.split("@")[1] || 0) },
                      ],
                    });
                    setPick((cur) => ({ ...cur, [key]: "" }));
                  }}
                >
                  {ui("common.add")}
                </button>
                <label>
                  {ui("common.qty")}
                  <input
                    type="number"
                    min={1}
                    value={drug.qty ?? 1}
                    onChange={(e) => editDrug(index, { qty: Number(e.target.value) })}
                  />
                </label>
                <label title={ui("gear.drugToggleHint")}>
                  <input
                    type="checkbox"
                    checked={Boolean(drug.active)}
                    onChange={(e) => editDrug(index, { active: e.target.checked })}
                  />
                  {ui("gear.inUse")}
                </label>
              </div>
            </div>
            <button
              className="btn danger"
              onClick={() => patchDrugs(owned.filter((_, i) => i !== index))}
            >
              {ui("common.delete")}
            </button>
          </div>
        );
      })}
      <button
        className="btn"
        onClick={() => patchDrugs([...owned, { name: "", grade: "Standard", qty: 1, parts: [] }])}
      >
        {ui("customDrug.mix")}
      </button>
    </div>
  );
}
