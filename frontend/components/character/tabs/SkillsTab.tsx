"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useMemo, useState } from "react";
import { SpecPicker } from "@/components/character/SpecPicker";
import { KNOW_CATS, KNOW_CAT_JA } from "@/lib/character/constants";
import { skillsoftBit, specBit } from "@/lib/character/bits";
import { mergeRatings, skillDice } from "@/lib/character/format";

export function SkillsTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  const [knowSearch, setKnowSearch] = useState("");
  const [knowCat, setKnowCat] = useState("all");
  const [customKnow, setCustomKnow] = useState("");
  const [customKnowCat, setCustomKnowCat] = useState("Street");
  const skillMax = d.skill_rating_max ?? 6;
  const groupMax = d.skill_group_max ?? 6;
  const career = Boolean(ch.career || d.career);

  const catalogKnowledge = new Set((catalog.skills.knowledge || []).map((item) => item.name));
  const filteredKnowledge = useMemo(() => {
    const q = knowSearch.trim().toLowerCase();
    return (catalog.skills.knowledge || [])
      .filter((item) => knowCat === "all" || item.category === knowCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      })
      .slice(0, 40);
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

  function patchExotic(next: { id?: string; skill_name: string; extra?: string; rating?: number }[]) {
    patch({ exotic_skills: next });
  }

  function draftExotic(id: string, next: { extra?: string; rating?: number }) {
    setCharacter({
      ...ch,
      exotic_skills: (ch.exotic_skills || []).map((row) => (row.id === id ? { ...row, ...next } : row)),
    });
  }

  return (
          <div className="card">
            <p className="muted">
              スキル {d.points.skills.used}/{d.points.skills.max} ・ グループ {d.points.skill_groups.used}/{d.points.skill_groups.max} ・ 知識 {d.points.knowledge.used}/{d.points.knowledge.max}
              {career ? " ・ キャリアはカルマで成長（上限 R" + skillMax + "）" : " ・ 専門化は1点"}
            </p>
            <h3>スキルグループ</h3>
            {catalog.skills.groups.map((g) => (
              <div className="skill-row" key={g}>
                <span>{tr(g)}</span>
                <input
                  type="range"
                  min={0}
                  max={groupMax}
                  value={ch.skill_groups[g] || 0}
                  onChange={(e) => setCharacter({ ...ch, skill_groups: { ...ch.skill_groups, [g]: Number(e.target.value) } })}
                  onMouseUp={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skill_groups: { ...ch.skill_groups, [g]: value } });
                  }}
                  onBlur={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skill_groups: { ...ch.skill_groups, [g]: value } });
                  }}
                />
                <b>{skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}</b>
              </div>
            ))}
            <h3>アクティブスキル</h3>
            {catalog.skills.skills.filter((s) => s.source === "SR5" && !s.name.includes("Exotic")).map((s) => {
              const specValue = ch.skill_specializations?.[s.name] || "";
              const hasSkill = (ch.skills[s.name] || 0) > 0 || (d.skill_totals[s.name] || 0) > 0 || (d.skillsoft?.[s.name] || 0) > 0;
              return (
              <div className="skill-row has-spec" key={s.id}>
                <span title={[s.attribute, ...(d.skill_bonus_notes?.[s.name] || [])].join(" / ")}>{tr(s.name)}</span>
                <input
                  type="range"
                  min={0}
                  max={skillMax + (d.skill_max_bonus?.[s.name] || 0)}
                  value={ch.skills[s.name] || d.skill_totals[s.name] || 0}
                  onChange={(e) => setCharacter({ ...ch, skills: { ...ch.skills, [s.name]: Number(e.target.value) } })}
                  onMouseUp={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                  onBlur={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                />
                <SpecPicker
                  options={[...(s.specs || []), ...(d.martial_spec_options?.[s.name] || [])]}
                  value={specValue}
                  disabled={!hasSkill}
                  tr={tr}
                  onDraft={(next) => draftSpec(s.name, next)}
                  onCommit={(next) => commitSpec(s.name, next)}
                />
                <b>
                  {skillDice(Math.max(d.skill_totals[s.name] || 0, d.skillsoft?.[s.name] || 0), d.skill_bonus?.[s.name])}
                  {skillsoftBit(d.skillsoft?.[s.name])}
                  {specBit(specValue, tr(specValue))}
                </b>
              </div>
              );
            })}
            <h3>Exoticスキル</h3>
            <p className="muted">対象の指定が技能そのものです。同じ Exotic を別対象で複数持てます。専門化の追加点は不要です。</p>
            {(d.exotic_skills || []).length ? (d.exotic_skills || []).map((row) => {
              const local = (ch.exotic_skills || []).find((item) => item.id === row.id);
              const extra = local?.extra ?? row.extra ?? "";
              const rating = local?.rating ?? row.rating;
              const bonus = d.skill_bonus?.[row.label] || d.skill_bonus?.[row.skill_name];
              return (
                <div className="skill-row has-spec can-delete" key={row.id}>
                  <span title={[row.attribute, ...(d.skill_bonus_notes?.[row.label] || d.skill_bonus_notes?.[row.skill_name] || [])].join(" / ")}>
                    {tr(row.skill_name)}
                  </span>
                  <input
                    type="range"
                    min={1}
                    max={row.rating_max}
                    value={rating}
                    onChange={(e) => draftExotic(row.id, { rating: Number(e.target.value) })}
                    onMouseUp={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, rating: value } : item
                      )));
                    }}
                    onBlur={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, rating: value } : item
                      )));
                    }}
                  />
                  <SpecPicker
                    options={row.options || []}
                    value={extra}
                    emptyLabel="対象"
                    placeholder="対象"
                    tr={tr}
                    onDraft={(next) => draftExotic(row.id, { extra: next })}
                    onCommit={(next) => {
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, extra: next } : item
                      )));
                    }}
                  />
                  <b>{skillDice(rating, bonus)}</b>
                  <button
                    className="btn danger"
                    onClick={() => patchExotic((ch.exotic_skills || []).filter((item) => item.id !== row.id))}
                  >
                    削除
                  </button>
                </div>
              );
            }) : (
              <p className="muted">まだありません。下のボタンから追加します。</p>
            )}
            <div className="option-row">
              {catalog.skills.skills.filter((s) => s.exotic || s.name.includes("Exotic")).map((s) => (
                <button
                  key={s.id}
                  className="btn"
                  onClick={() => patchExotic([...(ch.exotic_skills || []), { skill_name: s.name, extra: "", rating: 1 }])}
                >
                  {tr(s.name)} を追加
                </button>
              ))}
            </div>
            <h3>知識スキル</h3>
            <p className="muted">無料枠は (INT + LOG) × 2 ・ 母語は1つ無料。{career ? `キャリアのレーティングは1〜${skillMax}` : "作成時のレーティングは1〜6"}です。{career ? "追加はカルマ" : "専門化は知識点1"}です。</p>
            {Object.keys(d.skill_category_bonus || {}).length ? (
              <p className="muted">
                {Object.entries(d.skill_category_bonus || {})
                  .filter(([, bonus]) => bonus)
                  .map(([name, bonus]) => `${KNOW_CAT_JA[name] || tr(name)} ${bonus > 0 ? "+" : ""}${bonus}`)
                  .join(" ・ ")}
              </p>
            ) : null}
            {(d.knowledge_skills || []).length ? (d.knowledge_skills || []).map((row) => {
              const custom = !catalogKnowledge.has(row.name);
              const specValue = ch.skill_specializations?.[row.name] || row.spec || "";
              const knowSpec = (catalog.skills.knowledge || []).find((item) => item.name === row.name);
              return (
                <div className="know-row" key={row.name}>
                  <span title={[row.attribute, ...(d.skill_bonus_notes?.[row.name] || [])].join(" / ")}>
                    {tr(row.name)}
                    {custom ? " （カスタム）" : ""}
                  </span>
                  {custom ? (
                    <select
                      value={row.category}
                      onChange={(e) => patchKnowledge({
                        knowledge_categories: { ...(ch.knowledge_categories || {}), [row.name]: e.target.value },
                      })}
                    >
                      {KNOW_CATS.map((cat) => (
                        <option key={cat} value={cat}>{KNOW_CAT_JA[cat]}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="muted">{KNOW_CAT_JA[row.category] || row.category}</span>
                  )}
                  {row.native ? (
                    <span className="muted">無料</span>
                  ) : (
                    <input
                      type="range"
                      min={1}
                      max={skillMax}
                      value={ch.knowledge_skills[row.name] || row.rating}
                      onChange={(e) => setCharacter({
                        ...ch,
                        knowledge_skills: { ...ch.knowledge_skills, [row.name]: Number(e.target.value) },
                      })}
                      onMouseUp={(e) => {
                        const value = Number((e.target as HTMLInputElement).value);
                        patchKnowledge({ knowledge_skills: { ...ch.knowledge_skills, [row.name]: value } });
                      }}
                      onBlur={(e) => {
                        const value = Number((e.target as HTMLInputElement).value);
                        patchKnowledge({ knowledge_skills: { ...ch.knowledge_skills, [row.name]: value } });
                      }}
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
                    {row.native ? "母語" : skillDice(Math.max(row.rating, row.skillsoft || 0), d.skill_bonus?.[row.name])}
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
                        母語
                      </label>
                    ) : null}
                    <button className="btn danger" onClick={() => removeKnowledge(row.name)}>削除</button>
                  </span>
                </div>
              );
            }) : (
              <p className="muted">まだありません。カタログから追加するか、カスタム名で作れます。</p>
            )}
            <div className="option-row">
              <button className={`tab ${knowCat === "all" ? "active" : ""}`} onClick={() => setKnowCat("all")}>すべて</button>
              {KNOW_CATS.map((cat) => (
                <button key={cat} className={`tab ${knowCat === cat ? "active" : ""}`} onClick={() => setKnowCat(cat)}>
                  {KNOW_CAT_JA[cat]}
                </button>
              ))}
            </div>
            <input type="search" placeholder="知識スキルを検索" value={knowSearch} onChange={(e) => setKnowSearch(e.target.value)} />
            <div className="cyber-toolbar">
              <input
                type="text"
                placeholder="カスタム知識名"
                value={customKnow}
                onChange={(e) => setCustomKnow(e.target.value)}
              />
              <select value={customKnowCat} onChange={(e) => setCustomKnowCat(e.target.value)}>
                {KNOW_CATS.map((cat) => (
                  <option key={cat} value={cat}>{KNOW_CAT_JA[cat]}</option>
                ))}
              </select>
              <button className="btn primary" onClick={() => addKnowledge(customKnow, customKnowCat)}>カスタム追加</button>
            </div>
            <div className="quality-list">
              {filteredKnowledge.filter((item) => !ownedKnowledge.has(item.name)).map((item) => (
                <div className="quality-item" key={`${item.category}:${item.name}`}>
                  <div>
                    <b>{tr(item.name)}</b>
                    <div className="muted">{item.name} / {KNOW_CAT_JA[item.category] || item.category} / {item.attribute}</div>
                  </div>
                  <button className="btn primary" onClick={() => addKnowledge(item.name, item.category)}>追加</button>
                </div>
              ))}
            </div>
          </div>

  );
}
