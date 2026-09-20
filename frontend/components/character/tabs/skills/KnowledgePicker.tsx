"use client";
import { useMemo, useState } from "react";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { KNOW_CATS, knowCatLabel } from "@/lib/character/constants";
import { knowledgeEditor } from "./shared";

/** Adding a knowledge skill: from the list, by category and search, or by name. */
export function KnowledgePicker(props: TabPanelProps) {
  const { catalog, tr, ui } = props;
  const [knowSearch, setKnowSearch] = useState("");
  const [knowCat, setKnowCat] = useState("all");
  const [customKnow, setCustomKnow] = useState("");
  const [customKnowCat, setCustomKnowCat] = useState("Street");
  const know = knowledgeEditor(props);

  const matchedKnowledge = useMemo(() => {
    const q = knowSearch.trim().toLowerCase();
    return (catalog.skills.knowledge || [])
      .filter((item) => knowCat === "all" || item.category === knowCat)
      .filter((item) => {
        // `<PickerList>` applies the settings' book list; this used to
        // narrow to SR5 again underneath it
        if (!q) return true;
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      });
  }, [catalog, knowSearch, knowCat, tr]);

  function add(name: string, category?: string) {
    // a blank or duplicate name stays in the box, so it can be corrected
    if (know.add(name, category)) setCustomKnow("");
  }

  return (
    <>
      <div className="option-row">
        <button
          className={`tab ${knowCat === "all" ? "active" : ""}`}
          onClick={() => setKnowCat("all")}
        >
          {ui("common.all")}
        </button>
        {KNOW_CATS.map((cat) => (
          <button
            key={cat}
            className={`tab ${knowCat === cat ? "active" : ""}`}
            onClick={() => setKnowCat(cat)}
          >
            {knowCatLabel(cat, ui)}
          </button>
        ))}
      </div>
      <input
        type="search"
        placeholder={ui("skills.searchKnowledge")}
        aria-label={ui("skills.searchKnowledge")}
        value={knowSearch}
        onChange={(e) => setKnowSearch(e.target.value)}
      />
      <div className="cyber-toolbar">
        <input
          type="text"
          placeholder={ui("skills.customName")}
          aria-label={ui("skills.customName")}
          value={customKnow}
          onChange={(e) => setCustomKnow(e.target.value)}
        />
        <select value={customKnowCat} onChange={(e) => setCustomKnowCat(e.target.value)}>
          {KNOW_CATS.map((cat) => (
            <option key={cat} value={cat}>
              {knowCatLabel(cat, ui)}
            </option>
          ))}
        </select>
        <button className="btn primary" onClick={() => add(customKnow, customKnowCat)}>
          {ui("skills.addCustom")}
        </button>
      </div>
      <div className="quality-list">
        {/* the cut used to happen before the "already taken" filter, so a
            character with forty knowledge skills saw an empty list */}
        <PickerList items={matchedKnowledge.filter((item) => !know.owned.has(item.name))}>
          {(item) => (
            <div className="quality-item" key={`${item.category}:${item.name}`}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {knowCatLabel(item.category, ui)} / {item.attribute}
                </div>
              </div>
              <button className="btn primary" onClick={() => add(item.name, item.category)}>
                {ui("common.add")}
              </button>
            </div>
          )}
        </PickerList>
      </div>
    </>
  );
}
