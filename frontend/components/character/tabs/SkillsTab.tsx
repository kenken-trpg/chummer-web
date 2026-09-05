"use client";
import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useMemo, useState } from "react";
import { SpecPicker } from "@/components/character/SpecPicker";
import { RangeInput } from "@/components/character/RangeInput";
import {
  ACTIVE_SKILL_CATS,
  KNOW_CATS,
  knowCatLabel,
  skillCatLabel,
} from "@/lib/character/constants";
import { skillsoftBit, specBit } from "@/lib/character/bits";
import { skillDice } from "@/lib/character/format";

export function SkillsTab({
  catalog,
  character: ch,
  d,
  tr,
  trGroup,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [knowSearch, setKnowSearch] = useState("");
  const [knowCat, setKnowCat] = useState("all");
  const [customKnow, setCustomKnow] = useState("");
  const [customKnowCat, setCustomKnowCat] = useState("Street");
  const skillMax = d.skill_rating_max ?? 6;
  const groupMax = d.skill_group_max ?? 6;
  const career = Boolean(ch.career || d.career);
  const expertiseBySkill = useMemo(() => {
    const map = new Map<string, { spec: string; bonus: number; source?: string }>();
    for (const row of d.skill_expertises || []) {
      if (row.skill && row.spec) {
        map.set(row.skill, { spec: row.spec, bonus: row.bonus || 3, source: row.source });
      }
    }
    return map;
  }, [d.skill_expertises]);

  /**
   * The active skills in the order the rulebook prints them: by category
   * (SR5 p.130 — Combat, Physical, Social, Magical, Resonance, Technical,
   * Vehicle), alphabetical inside each. The vendored file's own order is
   * neither — it opens with Technical Active and runs Magical before Combat —
   * so a reader coming from the book or the official sheet had to hunt.
   *
   * `active_categories` is the catalog's copy of that order; the constant is
   * the fallback, and any category the catalog grows later lands after them
   * rather than being dropped.
   */
  const activeByCategory = useMemo(() => {
    const order = catalog.skills.active_categories?.length
      ? catalog.skills.active_categories
      : [...ACTIVE_SKILL_CATS];
    const rank = new Map(order.map((cat, i) => [cat, i]));
    const buckets = new Map<string, typeof catalog.skills.skills>();
    for (const s of catalog.skills.skills) {
      if (s.source !== "SR5" || s.name.includes("Exotic")) continue;
      const bucket = buckets.get(s.category);
      if (bucket) bucket.push(s);
      else buckets.set(s.category, [s]);
    }
    return [...buckets.entries()]
      .sort(([a], [b]) => (rank.get(a) ?? order.length) - (rank.get(b) ?? order.length))
      .map(([category, list]) => ({
        category,
        // English name, so the order matches the book rather than the reading
        // of whichever Japanese gloss we happen to ship.
        skills: [...list].sort((a, b) => a.name.localeCompare(b.name)),
      }));
  }, [catalog]);

  const catalogKnowledge = new Set((catalog.skills.knowledge || []).map((item) => item.name));
  const matchedKnowledge = useMemo(() => {
    const q = knowSearch.trim().toLowerCase();
    return (catalog.skills.knowledge || [])
      .filter((item) => knowCat === "all" || item.category === knowCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      });
  }, [catalog, knowSearch, knowCat, tr]);

  const ownedKnowledge = new Set((d.knowledge_skills || []).map((row) => row.name));

  function patchKnowledge(next: {
    knowledge_skills?: Record<string, number>;
    native_languages?: string[];
    knowledge_categories?: Record<string, string>;
  }) {
    patch({
      knowledge_skills: next.knowledge_skills ?? ch.knowledge_skills,
      native_languages: next.native_languages ?? ch.native_languages ?? [],
      knowledge_categories: next.knowledge_categories ?? ch.knowledge_categories ?? {},
    });
  }

  function addKnowledge(name: string, category?: string) {
    const trimmed = name.trim();
    if (!trimmed || ownedKnowledge.has(trimmed)) return;
    const ratings = { ...ch.knowledge_skills, [trimmed]: 1 };
    const cats = { ...(ch.knowledge_categories || {}) };
    const specItem = catalog.skills.knowledge.find((item) => item.name === trimmed);
    if (!specItem && category) cats[trimmed] = category;
    patchKnowledge({ knowledge_skills: ratings, knowledge_categories: cats });
    setCustomKnow("");
  }

  function setKnowledgeNative(name: string, on: boolean) {
    const ratings = { ...ch.knowledge_skills };
    const natives = [...(ch.native_languages || [])];
    const limit = Math.max(1, Number(d.native_language_limit || 1));
    if (on) {
      delete ratings[name];
      if (!natives.includes(name)) {
        if (natives.length >= limit) {
          const dropped = natives.shift();
          if (dropped) ratings[dropped] = ratings[dropped] || 1;
        }
        natives.push(name);
      }
      patchKnowledge({ knowledge_skills: ratings, native_languages: natives });
      return;
    }
    ratings[name] = ratings[name] || 1;
    patchKnowledge({
      knowledge_skills: ratings,
      native_languages: natives.filter((item) => item !== name),
    });
  }

  function removeKnowledge(name: string) {
    const ratings = { ...ch.knowledge_skills };
    delete ratings[name];
    const cats = { ...(ch.knowledge_categories || {}) };
    delete cats[name];
    const specs = { ...(ch.skill_specializations || {}) };
    delete specs[name];
    patch({
      knowledge_skills: ratings,
      native_languages: (ch.native_languages || []).filter((item) => item !== name),
      knowledge_categories: cats,
      skill_specializations: specs,
    });
  }

  /** The one-line "what am I about to drag" for an active-skill row: the
   *  linked attribute and category, plus whatever the engine says is already
   *  modifying it. */
  function skillHint(name: string, attribute: string, category: string): string {
    return [
      ui("skills.rowHint", {
        attr: attribute,
        category: skillCatLabel(category, ui),
        max: skillMax + (d.skill_max_bonus?.[name] || 0),
      }),
      ...(d.skill_bonus_notes?.[name] || []),
    ].join(" / ");
  }

  function draftSpec(name: string, value: string) {
    const next = { ...(ch.skill_specializations || {}) };
    if (value) next[name] = value;
    else delete next[name];
    setCharacter({ ...ch, skill_specializations: next });
  }

  function commitSpec(name: string, value: string) {
    const next = { ...(ch.skill_specializations || {}) };
    const trimmed = value.trim();
    if (trimmed) next[name] = trimmed;
    else delete next[name];
    setCharacter({ ...ch, skill_specializations: next });
    patch({ skill_specializations: next });
  }

  function patchExotic(
    next: { id?: string; skill_name: string; extra?: string; rating?: number }[],
  ) {
    patch({ exotic_skills: next });
  }

  function draftExotic(id: string, next: { extra?: string; rating?: number }) {
    setCharacter({
      ...ch,
      exotic_skills: (ch.exotic_skills || []).map((row) =>
        row.id === id ? { ...row, ...next } : row,
      ),
    });
  }

  return (
    <div className="card">
      <p className="muted">
        {ui("skills.points", {
          skills: `${d.points.skills.used}/${d.points.skills.max}`,
          groups: `${d.points.skill_groups.used}/${d.points.skill_groups.max}`,
          knowledge: `${d.points.knowledge.used}/${d.points.knowledge.max}`,
        })}
        {career ? ui("skills.careerNote", { max: skillMax }) : ui("skills.chargenNote")}
      </p>
      <h3>{ui("skills.groups")}</h3>
      {catalog.skills.groups.map((g) => (
        <div className="skill-row" key={g}>
          <span title={ui("skills.groupHint", { group: trGroup(g), max: groupMax })}>
            {trGroup(g)}
          </span>
          <RangeInput
            min={0}
            max={groupMax}
            value={ch.skill_groups[g] || 0}
            label={trGroup(g)}
            title={ui("skills.groupHint", { group: trGroup(g), max: groupMax })}
            onDraft={(value) =>
              setCharacter({ ...ch, skill_groups: { ...ch.skill_groups, [g]: value } })
            }
            onCommit={(value) => patch({ skill_groups: { ...ch.skill_groups, [g]: value } })}
          />
          <b>{skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}</b>
        </div>
      ))}
      <h3>{ui("skills.active")}</h3>
      {activeByCategory.map(({ category, skills }) => (
        <div key={category}>
          <h4 className="skill-cat">{skillCatLabel(category, ui)}</h4>
          {skills.map((s) => {
            const expertise = expertiseBySkill.get(s.name);
            const specValue = expertise?.spec || ch.skill_specializations?.[s.name] || "";
            const hasSkill =
              (ch.skills[s.name] || 0) > 0 ||
              (d.skill_totals[s.name] || 0) > 0 ||
              (d.skillsoft?.[s.name] || 0) > 0;
            return (
              <div className="skill-row has-spec" key={s.id}>
                <span title={skillHint(s.name, s.attribute, s.category)}>{tr(s.name)}</span>
                <RangeInput
                  min={0}
                  max={skillMax + (d.skill_max_bonus?.[s.name] || 0)}
                  value={ch.skills[s.name] || d.skill_totals[s.name] || 0}
                  label={tr(s.name)}
                  title={skillHint(s.name, s.attribute, s.category)}
                  onDraft={(value) =>
                    setCharacter({ ...ch, skills: { ...ch.skills, [s.name]: value } })
                  }
                  onCommit={(value) => patch({ skills: { ...ch.skills, [s.name]: value } })}
                />
                <SpecPicker
                  options={[...(s.specs || []), ...(d.martial_spec_options?.[s.name] || [])]}
                  value={specValue}
                  disabled={!hasSkill || Boolean(expertise)}
                  tr={tr}
                  onDraft={(next) => draftSpec(s.name, next)}
                  onCommit={(next) => commitSpec(s.name, next)}
                />
                <b>
                  {skillDice(
                    Math.max(d.skill_totals[s.name] || 0, d.skillsoft?.[s.name] || 0),
                    d.skill_bonus?.[s.name],
                  )}
                  {skillsoftBit(d.skillsoft?.[s.name])}
                  {specBit(specValue, tr(specValue), expertise?.bonus || 2)}
                </b>
              </div>
            );
          })}
        </div>
      ))}
      <h3>{ui("skills.exotic")}</h3>
      <p className="muted">{ui("skills.exoticNote")}</p>
      {(d.exotic_skills || []).length ? (
        (d.exotic_skills || []).map((row) => {
          const local = (ch.exotic_skills || []).find((item) => item.id === row.id);
          const extra = local?.extra ?? row.extra ?? "";
          const rating = local?.rating ?? row.rating;
          const bonus = d.skill_bonus?.[row.label] || d.skill_bonus?.[row.skill_name];
          return (
            <div className="skill-row has-spec can-delete" key={row.id}>
              <span
                title={[
                  row.attribute,
                  ...(d.skill_bonus_notes?.[row.label] ||
                    d.skill_bonus_notes?.[row.skill_name] ||
                    []),
                ].join(" / ")}
              >
                {tr(row.skill_name)}
              </span>
              <RangeInput
                min={1}
                max={row.rating_max}
                value={rating}
                label={tr(row.skill_name)}
                title={ui("skills.ratingHint", { max: row.rating_max })}
                onDraft={(value) => draftExotic(row.id, { rating: value })}
                onCommit={(value) =>
                  patchExotic(
                    (ch.exotic_skills || []).map((item) =>
                      item.id === row.id ? { ...item, rating: value } : item,
                    ),
                  )
                }
              />
              <SpecPicker
                options={row.options || []}
                value={extra}
                emptyLabel={ui("common.target")}
                placeholder={ui("common.target")}
                tr={tr}
                onDraft={(next) => draftExotic(row.id, { extra: next })}
                onCommit={(next) => {
                  patchExotic(
                    (ch.exotic_skills || []).map((item) =>
                      item.id === row.id ? { ...item, extra: next } : item,
                    ),
                  );
                }}
              />
              <b>{skillDice(rating, bonus)}</b>
              <button
                className="btn danger"
                onClick={() =>
                  patchExotic((ch.exotic_skills || []).filter((item) => item.id !== row.id))
                }
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })
      ) : (
        <p className="muted">{ui("skills.emptyExotic")}</p>
      )}
      <div className="option-row">
        {catalog.skills.skills
          .filter((s) => s.exotic || s.name.includes("Exotic"))
          .map((s) => (
            <button
              key={s.id}
              className="btn"
              onClick={() =>
                patchExotic([
                  ...(ch.exotic_skills || []),
                  { skill_name: s.name, extra: "", rating: 1 },
                ])
              }
            >
              {ui("skills.addNamed", { name: tr(s.name) })}
            </button>
          ))}
      </div>
      <h3>{ui("skills.knowledge")}</h3>
      <p className="muted">
        {ui("skills.knowledgeFree")}
        {career
          ? ui("skills.knowledgeCareerRange", { max: skillMax })
          : ui("skills.knowledgeChargenRange")}
        {ui("skills.rangeSuffix")}
        {career ? ui("skills.knowledgeCareerCost") : ui("skills.knowledgeChargenCost")}
      </p>
      {Object.keys(d.skill_category_bonus || {}).length ? (
        <p className="muted">
          {Object.entries(d.skill_category_bonus || {})
            .filter(([, bonus]) => bonus)
            .map(
              ([name, bonus]) =>
                `${(KNOW_CATS as readonly string[]).includes(name) ? knowCatLabel(name, ui) : tr(name)} ${
                  bonus > 0 ? "+" : ""
                }${bonus}`,
            )
            .join(` ${ui("common.termSep")} `)}
        </p>
      ) : null}
      {(d.knowledge_skills || []).length ? (
        (d.knowledge_skills || []).map((row) => {
          const custom = !catalogKnowledge.has(row.name);
          const specValue = ch.skill_specializations?.[row.name] || row.spec || "";
          const knowSpec = (catalog.skills.knowledge || []).find((item) => item.name === row.name);
          return (
            <div className="know-row" key={row.name}>
              <span title={[row.attribute, ...(d.skill_bonus_notes?.[row.name] || [])].join(" / ")}>
                {tr(row.name)}
                {custom ? ui("skills.custom") : ""}
              </span>
              {custom ? (
                <select
                  value={row.category}
                  onChange={(e) =>
                    patchKnowledge({
                      knowledge_categories: {
                        ...(ch.knowledge_categories || {}),
                        [row.name]: e.target.value,
                      },
                    })
                  }
                >
                  {KNOW_CATS.map((cat) => (
                    <option key={cat} value={cat}>
                      {knowCatLabel(cat, ui)}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="muted">{knowCatLabel(row.category, ui)}</span>
              )}
              {row.native ? (
                <span className="muted">{ui("skills.free")}</span>
              ) : (
                <RangeInput
                  min={1}
                  max={skillMax}
                  value={ch.knowledge_skills[row.name] || row.rating}
                  label={tr(row.name)}
                  title={ui("skills.ratingHint", { max: skillMax })}
                  onDraft={(value) =>
                    setCharacter({
                      ...ch,
                      knowledge_skills: { ...ch.knowledge_skills, [row.name]: value },
                    })
                  }
                  onCommit={(value) =>
                    patchKnowledge({
                      knowledge_skills: { ...ch.knowledge_skills, [row.name]: value },
                    })
                  }
                />
              )}
              <SpecPicker
                options={knowSpec?.specs || []}
                value={specValue}
                tr={tr}
                onDraft={(next) => draftSpec(row.name, next)}
                onCommit={(next) => commitSpec(row.name, next)}
              />
              <b>
                {row.native
                  ? ui("skills.native")
                  : skillDice(Math.max(row.rating, row.skillsoft || 0), d.skill_bonus?.[row.name])}
                {row.native ? null : skillsoftBit(row.skillsoft)}
                {specBit(specValue, tr(specValue))}
              </b>
              <span className="option-row" style={{ margin: 0, gap: 6 }}>
                {row.category === "Language" ? (
                  <label className="native">
                    <input
                      type="checkbox"
                      checked={row.native}
                      onChange={(e) => setKnowledgeNative(row.name, e.target.checked)}
                    />
                    {ui("skills.native")}
                  </label>
                ) : null}
                <button className="btn danger" onClick={() => removeKnowledge(row.name)}>
                  {ui("common.delete")}
                </button>
              </span>
            </div>
          );
        })
      ) : (
        <p className="muted">{ui("skills.emptyKnowledge")}</p>
      )}
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
        <button className="btn primary" onClick={() => addKnowledge(customKnow, customKnowCat)}>
          {ui("skills.addCustom")}
        </button>
      </div>
      <div className="quality-list">
        {/* the cut used to happen before the "already taken" filter, so a
            character with forty knowledge skills saw an empty list */}
        <PickerList
          items={matchedKnowledge.filter((item) => !ownedKnowledge.has(item.name))}
          note={knowSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => (
            <div className="quality-item" key={`${item.category}:${item.name}`}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {knowCatLabel(item.category, ui)} / {item.attribute}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() => addKnowledge(item.name, item.category)}
              >
                {ui("common.add")}
              </button>
            </div>
          )}
        </PickerList>
      </div>
    </div>
  );
}
