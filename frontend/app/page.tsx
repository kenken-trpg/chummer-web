"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Catalog, Character, InstalledAdeptPower, InstalledWare, MentorInfo, PriorityCategory, PriorityLetter, SkillPickSlot, WareCatalogItem, WareInstall } from "@/lib/types";

const CATS: { key: PriorityCategory; label: string }[] = [
  { key: "Heritage", label: "メタタイプ" },
  { key: "Attributes", label: "属性" },
  { key: "Talent", label: "魔法/レゾナンス" },
  { key: "Skills", label: "スキル" },
  { key: "Resources", label: "資金" },
];
const LETTERS: PriorityLetter[] = ["A", "B", "C", "D", "E"];
const ATTRS = ["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA", "EDG", "MAG", "RES"] as const;
const ATTR_JA: Record<string, string> = {
  BOD: "BOD 体",
  AGI: "AGI 敏",
  REA: "REA 反",
  STR: "STR 力",
  WIL: "WIL 意",
  LOG: "LOG 論",
  INT: "INT 直",
  CHA: "CHA 魅",
  EDG: "EDG 縁",
  MAG: "MAG 魔力",
  RES: "RES 共振力",
};

type Tab = "priority" | "meta" | "attrs" | "skills" | "qualities" | "cyber" | "bio" | "adept";

function formatPoints(value: number) {
  const rounded = Math.round(value * 100) / 100;
  return String(rounded);
}

function removeWareTree(items: WareInstall[], id: string): WareInstall[] {
  const drop = new Set<string>([id]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const row of items) {
      if (row.parent_id && drop.has(row.parent_id) && !drop.has(row.id)) {
        drop.add(row.id);
        grew = true;
      }
    }
  }
  return items.filter((row) => !drop.has(row.id));
}

function wareBounds(item: WareCatalogItem, ranges?: Record<string, { min: number; max: number }>) {
  return ranges?.[item.id] || { min: item.minrating, max: item.maxrating };
}

function hideFromWareCatalog(item: WareCatalogItem, kind: "cyberware" | "bioware") {
  if (item.requireparent || item.formula_rating) return true;
  const same = item.required?.[kind] || [];
  const other = item.required?.[kind === "bioware" ? "cyberware" : "bioware"] || [];
  return same.length > 0 && other.length === 0;
}

const SIDE_JA: Record<string, string> = { Left: "左", Right: "右" };

function sideSlotKey(item: WareCatalogItem) {
  return (item.limbslot || item.id || "").toLowerCase();
}

function nextFreeSide(items: WareInstall[], catalogItems: WareCatalogItem[], ware: WareCatalogItem) {
  if (!ware.selectside) return undefined;
  const slot = sideSlotKey(ware);
  const used = new Set(
    items
      .filter((row) => !row.parent_id && row.side)
      .filter((row) => {
        const spec = catalogItems.find((w) => w.id === row.ware_id);
        return spec?.selectside && sideSlotKey(spec) === slot;
      })
      .map((row) => row.side),
  );
  return used.has("Left") && !used.has("Right") ? "Right" : "Left";
}

const REDLINER_SLOT_JA: Record<string, string> = { arm: "腕", leg: "脚", torso: "胴", skull: "頭蓋" };

function skillDice(rating: number, bonus?: number) {
  if (!bonus) return String(rating);
  const sign = bonus > 0 ? "+" : "";
  return `${rating} ${sign}${bonus}`;
}

function dropSkillPicksForPrefix(picks: Record<string, string> | undefined, prefixes: string[]) {
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    if (prefixes.some((prefix) => key.startsWith(prefix))) delete next[key];
  }
  return next;
}

function dropRemovedWarePicks(picks: Record<string, string> | undefined, remaining: WareInstall[]) {
  const keep = new Set(remaining.map((row) => row.id));
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    const match = key.match(/^ware:([^:]+):/);
    if (match && !keep.has(match[1])) delete next[key];
  }
  return next;
}

function SkillPickSelects(props: {
  slots: SkillPickSlot[];
  tr: (name: string) => string;
  onPick: (key: string, skill: string) => void;
}) {
  if (!props.slots.length) return null;
  return (
    <div className="skill-picks">
      {props.slots.map((slot) => (
        <label key={slot.key}>
          {props.tr(slot.source)} のスキル
          {slot.bonus ? ` ${slot.bonus > 0 ? "+" : ""}${slot.bonus}` : ""}
          {slot.max ? ` 上限+${slot.max}` : ""}
          <select value={slot.picked} onChange={(e) => props.onPick(slot.key, e.target.value)}>
            <option value="">選択してください</option>
            {slot.options.map((name) => (
              <option key={name} value={name}>{props.tr(name)}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}

function limbQualityLine(q: NonNullable<Character["derived"]["limb_quality"]>) {
  const bits: string[] = [];
  if (q.limb_bonus) bits.push(`肢 STR/AGI +${q.limb_bonus}`);
  for (const [key, value] of Object.entries(q.attribute_bonus || {})) {
    if (key === "STR" || key === "AGI" || !value) continue;
    bits.push(`${key} +${value}`);
  }
  if (q.cm_physical) bits.push(`物理CM ${q.cm_physical}`);
  const effect = bits.length ? bits.join(" ・ ") : "ボーナスなし";
  const parts = (q.include || ["arm", "leg"]).map((slot) => REDLINER_SLOT_JA[slot] || slot).join("・");
  return `リム本数 Quality ${q.count}本（${q.pairs}組 / ${parts}） ・ ${effect}`;
}

function WareRow(props: {
  item: InstalledWare;
  childrenItems: InstalledWare[];
  catalogItems: WareCatalogItem[];
  grades: { name: string; ess: number; cost: number }[];
  kind: "cyberware" | "bioware";
  tr: (name: string) => string;
  slotValue: string;
  wareRanges?: Record<string, { min: number; max: number }>;
  onSlotChange: (wareId: string) => void;
  onPatchRow: (id: string, next: Partial<WareInstall>) => void;
  onRemove: (id: string) => void;
  onAddChild: (wareId: string) => void;
  pickSlots?: SkillPickSlot[];
  onSkillPick?: (key: string, skill: string) => void;
  nested?: boolean;
}) {
  const { item, childrenItems, catalogItems, grades, kind, tr, slotValue, wareRanges, onSlotChange, onPatchRow, onRemove, onAddChild, pickSlots, onSkillPick, nested } = props;
  const spec = catalogItems.find((w) => w.id === item.ware_id);
  const slots = (spec?.allow_subsystems || []).filter(Boolean);
  const slotOptions = catalogItems.filter((w) => {
    if (w.id === item.ware_id) return false;
    if ((w.required?.[kind] || []).includes(item.name)) return true;
    return slots.includes(w.category) && Boolean(w.plugin || w.requireparent);
  });
  const rowGrades = grades.filter((g) => !(spec?.bannedgrades || []).includes(g.name));
  const chosen = slotValue || slotOptions[0]?.id || "";
  const capMax = item.capacity_max || 0;
  const ratingMin = item.rating_min ?? spec?.minrating ?? 1;
  const ratingMax = item.rating_max ?? spec?.maxrating ?? 1;
  return (
    <div className={`cyber-item${nested ? " nested" : ""}`}>
      <div>
        <b>{tr(item.name)}{item.side ? `（${SIDE_JA[item.side] || item.side}）` : ""}{item.included ? "（同梱）" : ""}</b>
        <div className="muted">
          {item.name} / {item.category} / ESS −{item.essence} / {item.nuyen.toLocaleString()}¥ / {item.source}
          {capMax > 0 ? <span className="cap"> ・ 容量 {item.capacity_used ?? 0}/{capMax}</span> : null}
          {item.limb_str != null ? <span className="cap"> ・ 肢 STR {item.limb_str} / AGI {item.limb_agi}</span> : null}
        </div>
        <div className="cyber-controls">
          {spec?.selectside && !item.parent_id && !item.included ? (
            <label>
              左右
              <select value={item.side || "Left"} onChange={(e) => onPatchRow(item.id, { side: e.target.value })}>
                <option value="Left">左</option>
                <option value="Right">右</option>
              </select>
            </label>
          ) : null}
          {spec && ratingMax > ratingMin && !item.included ? (
            <label>
              レーティング
              <input
                type="number"
                min={ratingMin}
                max={ratingMax}
                value={item.rating}
                onChange={(e) => onPatchRow(item.id, { rating: Number(e.target.value) })}
              />
            </label>
          ) : null}
          {!item.included && !spec?.forcegrade ? (
            <label>
              グレード
              <select value={item.grade} onChange={(e) => onPatchRow(item.id, { grade: e.target.value })}>
                {rowGrades.map((g) => (
                  <option key={g.name} value={g.name}>{g.name} (ESS×{g.ess} / ¥×{g.cost})</option>
                ))}
              </select>
            </label>
          ) : null}
          {spec?.has_wireless ? (
            <label>
              <input
                type="checkbox"
                checked={item.wireless}
                onChange={(e) => onPatchRow(item.id, { wireless: e.target.checked })}
              />
              ワイヤレス
            </label>
          ) : null}
        </div>
        {onSkillPick ? (
          <SkillPickSelects
            slots={(pickSlots || []).filter((slot) => slot.source_id === item.id)}
            tr={tr}
            onPick={onSkillPick}
          />
        ) : null}
        {childrenItems.map((child) => (
          <WareRow
            key={child.id}
            item={child}
            childrenItems={[]}
            catalogItems={catalogItems}
            grades={grades}
            kind={kind}
            tr={tr}
            slotValue=""
            wareRanges={wareRanges}
            onSlotChange={() => undefined}
            onPatchRow={onPatchRow}
            onRemove={onRemove}
            onAddChild={() => undefined}
            pickSlots={pickSlots}
            onSkillPick={onSkillPick}
            nested
          />
        ))}
        {slotOptions.length > 0 ? (
          <div className="slot-picker">
            <select value={chosen} onChange={(e) => onSlotChange(e.target.value)}>
              {slotOptions.map((w) => {
                const range = wareBounds(w, wareRanges);
                const showRange = range.max > range.min || range.max > 1;
                return (
                  <option key={w.id} value={w.id}>
                    {tr(w.name)} / {w.capacity ? `[${w.capacity}]` : w.category}{showRange ? ` R${range.min}-${range.max}` : ""}
                  </option>
                );
              })}
            </select>
            <button className="btn primary" disabled={!chosen} onClick={() => chosen && onAddChild(chosen)}>スロットに追加</button>
          </div>
        ) : null}
      </div>
      {item.included ? <span className="muted">同梱</span> : <button className="btn danger" onClick={() => onRemove(item.id)}>削除</button>}
    </div>
  );
}

function selectLabel(kind?: string | null) {
  if (kind === "skill") return "スキル";
  if (kind === "attribute") return "属性";
  if (kind === "spell") return "呪文";
  return "対象";
}

function MentorPicker({
  catalog,
  mentor,
  ch,
  tr,
  onPatch,
}: {
  catalog: Catalog;
  mentor?: MentorInfo | null;
  ch: Character;
  tr: (name: string) => string;
  onPatch: (body: Record<string, unknown>) => void;
}) {
  return (
    <div className="cyber-item">
      <div>
        <b>メンタースピリット</b>
        <div className="muted">{mentor ? `${tr(mentor.name)} / ${mentor.source}` : "未選択"}</div>
        <div className="cyber-controls">
          <label>
            メンター
            <select value={ch.mentor_id || ""} onChange={(e) => onPatch({ mentor_id: e.target.value, mentor_choices: [], mentor_extras: {} })}>
              <option value="">選択してください</option>
              {(catalog.mentors || []).map((item) => (
                <option key={item.id} value={item.id}>{tr(item.name)}</option>
              ))}
            </select>
          </label>
        </div>
        {mentor?.advantage ? <p className="muted">{mentor.advantage}</p> : null}
        {(mentor?.choices || []).map((choice) => (
          <label key={choice.name} className="skill-row">
            <input
              type="checkbox"
              checked={choice.selected}
              onChange={() => {
                const current = new Set(ch.mentor_choices || mentor.choices.filter((row) => row.selected).map((row) => row.name));
                if (choice.selected) current.delete(choice.name);
                else {
                  if (choice.set) {
                    mentor.choices.filter((row) => row.set === choice.set).forEach((row) => current.delete(row.name));
                  }
                  current.add(choice.name);
                }
                onPatch({ mentor_choices: [...current] });
              }}
            />
            <span>{choice.name}</span>
            {choice.extra_options.length ? (
              <select
                value={choice.extra || ""}
                onChange={(e) => onPatch({ mentor_extras: { ...(ch.mentor_extras || {}), [choice.name]: e.target.value } })}
              >
                <option value="">対象を選択</option>
                {choice.extra_options.map((name) => (
                  <option key={name} value={name}>{tr(name)}</option>
                ))}
              </select>
            ) : null}
          </label>
        ))}
      </div>
    </div>
  );
}

function ExtraSelect({
  item,
  tr,
  onChange,
}: {
  item: InstalledAdeptPower;
  tr: (name: string) => string;
  onChange: (extra: string) => void;
}) {
  if (!item.select) return null;
  return (
    <label>
      {selectLabel(item.select)}
      <select value={item.extra || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">選択してください</option>
        {item.options.map((name) => (
          <option key={name} value={name}>{item.select === "attribute" ? (ATTR_JA[name] || name) : tr(name)}</option>
        ))}
      </select>
    </label>
  );
}

export default function Page() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [ch, setCh] = useState<Character | null>(null);
  const [tab, setTab] = useState<Tab>("priority");
  const [qSearch, setQSearch] = useState("");
  const [cySearch, setCySearch] = useState("");
  const [cyCat, setCyCat] = useState("all");
  const [addGrade, setAddGrade] = useState("Standard");
  const [bioSearch, setBioSearch] = useState("");
  const [bioCat, setBioCat] = useState("all");
  const [bioGrade, setBioGrade] = useState("Standard");
  const [powerSearch, setPowerSearch] = useState("");
  const [enhSearch, setEnhSearch] = useState("");
  const [qiSearch, setQiSearch] = useState("");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const busy = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        const [cat, created] = await Promise.all([api.catalog(), api.create("Runner")]);
        setCatalog(cat);
        setCh(created);
      } catch (e) {
        setError(e instanceof Error ? e.message : "起動に失敗しました");
      }
    })();
  }, []);

  async function patch(body: Record<string, unknown>) {
    if (!ch || busy.current) return;
    busy.current = true;
    try {
      setCh(await api.patch(ch.id, body));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      busy.current = false;
    }
  }

  const tr = (name: string) => catalog?.translations[name] || name;

  const filteredQualities = useMemo(() => {
    if (!catalog) return [];
    const q = qSearch.trim().toLowerCase();
    return catalog.qualities
      .filter((item) => !q || item.name.toLowerCase().includes(q) || tr(item.name).includes(qSearch))
      .slice(0, 80);
  }, [catalog, qSearch]);

  const cyberCats = useMemo(() => {
    if (!catalog) return [];
    return [...new Set(catalog.cyberware.items.filter((w) => !hideFromWareCatalog(w, "cyberware")).map((w) => w.category))].sort();
  }, [catalog]);

  const filteredCyber = useMemo(() => {
    if (!catalog) return [];
    const q = cySearch.trim().toLowerCase();
    return catalog.cyberware.items
      .filter((w) => !hideFromWareCatalog(w, "cyberware"))
      .filter((w) => cyCat === "all" || w.category === cyCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(cySearch))
      .slice(0, 80);
  }, [catalog, cySearch, cyCat]);

  const bioCats = useMemo(() => {
    if (!catalog) return [];
    return [...new Set((catalog.bioware?.items || []).filter((w) => !hideFromWareCatalog(w, "bioware")).map((w) => w.category))].sort();
  }, [catalog]);

  const filteredBio = useMemo(() => {
    if (!catalog) return [];
    const q = bioSearch.trim().toLowerCase();
    return (catalog.bioware?.items || [])
      .filter((w) => !hideFromWareCatalog(w, "bioware"))
      .filter((w) => bioCat === "all" || w.category === bioCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(bioSearch))
      .slice(0, 80);
  }, [catalog, bioSearch, bioCat]);

  const filteredPowers = useMemo(() => {
    if (!catalog) return [];
    const q = powerSearch.trim().toLowerCase();
    return (catalog.powers || [])
      .filter((item) => !q ? item.source === "SR5" : item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q))
      .slice(0, 80);
  }, [catalog, powerSearch]);

  function download() {
    if (!ch) return;
    const blob = new Blob([JSON.stringify(ch, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${ch.name || "character"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function onImport(file: File) {
    const payload = JSON.parse(await file.text());
    setCh(await api.import(payload));
  }

  if (error && !ch) {
    return <div className="main"><p className="errors">{error}</p></div>;
  }
  if (!catalog || !ch) {
    return <div className="main">読み込み中…</div>;
  }

  const d = ch.derived;
  const spec = d.metatype_info.attributes;
  const table = catalog.priority_table;

  return (
    <div className="app">
      <div className="main">
        <h1>CHUMMER WEB</h1>
        <p className="sub">非公式 Shadowrun 5e キャラクター作成。Catalyst / Topps 非提携。データは Chummer5a (GPL-3.0)。</p>

        <div className="toolbar">
          <input value={ch.name} onChange={(e) => setCh({ ...ch, name: e.target.value })} onBlur={(e) => patch({ name: e.target.value })} />
          <button className="btn primary" onClick={download}>JSON保存</button>
          <button className="btn" onClick={() => fileRef.current?.click()}>JSON読込</button>
          <input ref={fileRef} type="file" accept="application/json" hidden onChange={(e) => e.target.files && onImport(e.target.files[0])} />
        </div>

        <div className="tabs">
          {([
            ["priority", "優先度"],
            ["meta", "メタタイプ"],
            ["attrs", "属性"],
            ["skills", "スキル"],
            ["qualities", "クオリティ"],
            ["cyber", "サイバー"],
            ["bio", "バイオ"],
            ...(d.enabled_tabs.includes("adept") ? [["adept", "アデプト"] as const] : []),
          ] as const).map(([k, label]) => (
            <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>{label}</button>
          ))}
        </div>

        {tab === "priority" && (
          <div className="card">
            <table>
              <thead>
                <tr>
                  <th></th>
                  {LETTERS.map((l) => <th key={l}>{l}</th>)}
                </tr>
              </thead>
              <tbody>
                {CATS.map((cat) => (
                  <tr key={cat.key}>
                    <td className="rowhead">{cat.label}</td>
                    {LETTERS.map((letter) => {
                      const cell = table[cat.key][letter];
                      const takenBy = CATS.find((c) => ch.priorities[c.key] === letter && c.key !== cat.key);
                      return (
                        <td key={letter}>
                          <button
                            className={`choice ${ch.priorities[cat.key] === letter ? "selected" : ""}`}
                            onClick={() => {
                              const next = { ...ch.priorities };
                              if (takenBy) next[takenBy.key] = next[cat.key];
                              next[cat.key] = letter;
                              const extra: Record<string, unknown> = { priorities: next };
                              if (cat.key === "Talent") {
                                const options = table.Talent[letter].talents.filter((t) => t.name !== "Mundane");
                                extra.talent =
                                  letter === "E"
                                    ? "Mundane"
                                    : options.some((t) => t.name === ch.talent)
                                      ? ch.talent
                                      : options[0]?.name || "Magician";
                              }
                              patch(extra);
                            }}
                          >
                            {cell?.name?.replace(/^[A-E]\s*-\s*/, "") || letter}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">A〜E は各1回。クリックで入れ替えます。</p>
          </div>
        )}

        {tab === "meta" && (
          <div className="card">
            <div className="grid">
              {table.Heritage[ch.priorities.Heritage].metatypes.map((m) => (
                <button key={m.name} className={`choice ${ch.metatype === m.name ? "selected" : ""}`} onClick={() => patch({ metatype: m.name, metavariant: null })}>
                  <b>{tr(m.name)}</b>
                  <div className="muted">{m.name} / 特殊点 {m.special}</div>
                </button>
              ))}
            </div>
            {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants?.length ? (
              <div style={{ marginTop: 12 }}>
                <label className="muted">メタバリアント</label>
                <select
                  value={ch.metavariant || ""}
                  onChange={(e) => patch({ metavariant: e.target.value || null })}
                >
                  <option value="">なし（{tr(ch.metatype)}）</option>
                  {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants.map((v) => (
                    <option key={v.name} value={v.name}>{tr(v.name)} ({v.name})</option>
                  ))}
                </select>
              </div>
            ) : null}
            <div style={{ marginTop: 12 }}>
              <label className="muted">タレント</label>
              <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
                {table.Talent[ch.priorities.Talent].talents.map((t) => (
                  <option key={t.name} value={t.name}>{t.label || t.name}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {tab === "attrs" && (
          <div className="card">
            {ATTRS.map((key) => {
              const hidden = (key === "MAG" && !d.enabled_tabs.includes("MAG")) || (key === "RES" && !d.enabled_tabs.includes("RES"));
              if (hidden) return null;
              const range = spec[key] || { min: 1, max: 6, aug: 6 };
              return (
                <div className="attr-row" key={key}>
                  <span>{ATTR_JA[key]}</span>
                  <input
                    type="range"
                    min={range.min}
                    max={range.max}
                    value={ch.attributes[key] ?? range.min}
                    onChange={(e) => {
                      const attributes = { ...ch.attributes, [key]: Number(e.target.value) };
                      setCh({ ...ch, attributes });
                    }}
                    onMouseUp={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onTouchEnd={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onBlur={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                  />
                  <b>
                    {d.totals[key]} <span className="muted">/{range.max}</span>
                    {d.limb_replace && (key === "STR" || key === "AGI") ? (
                      <span className="muted"> 肉{key === "STR" ? d.limb_replace.meat_str : d.limb_replace.meat_agi}</span>
                    ) : null}
                  </b>
                </div>
              );
            })}
            <p className="muted">属性点 {d.points.attributes.used}/{d.points.attributes.max} ・ 特殊点 {d.points.special.used}/{d.points.special.max}</p>
          </div>
        )}

        {tab === "skills" && (
          <div className="card">
            <p className="muted">スキル {d.points.skills.used}/{d.points.skills.max} ・ グループ {d.points.skill_groups.used}/{d.points.skill_groups.max}</p>
            <h3>スキルグループ</h3>
            {catalog.skills.groups.map((g) => (
              <div className="skill-row" key={g}>
                <span>{tr(g)}</span>
                <input
                  type="range"
                  min={0}
                  max={6}
                  value={ch.skill_groups[g] || 0}
                  onChange={(e) => setCh({ ...ch, skill_groups: { ...ch.skill_groups, [g]: Number(e.target.value) } })}
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
            {catalog.skills.skills.filter((s) => s.source === "SR5" && !s.name.includes("Exotic")).map((s) => (
              <div className="skill-row" key={s.id}>
                <span title={[s.attribute, ...(d.skill_bonus_notes?.[s.name] || [])].join(" / ")}>{tr(s.name)}</span>
                <input
                  type="range"
                  min={0}
                  max={6 + (d.skill_max_bonus?.[s.name] || 0)}
                  value={ch.skills[s.name] || d.skill_totals[s.name] || 0}
                  onChange={(e) => setCh({ ...ch, skills: { ...ch.skills, [s.name]: Number(e.target.value) } })}
                  onMouseUp={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                  onBlur={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                />
                <b>{skillDice(d.skill_totals[s.name] || 0, d.skill_bonus?.[s.name])}</b>
              </div>
            ))}
            {Object.keys(d.skill_category_bonus || {}).length ? (
              <>
                <h3>知識スキルカテゴリ</h3>
                <p className="muted">
                  {Object.entries(d.skill_category_bonus || {})
                    .filter(([, bonus]) => bonus)
                    .map(([name, bonus]) => `${tr(name)} ${bonus > 0 ? "+" : ""}${bonus}`)
                    .join(" ・ ")}
                </p>
                {Object.entries(ch.knowledge_skills || {}).filter(([, rating]) => rating > 0).map(([name, rating]) => (
                  <div className="skill-row" key={name}>
                    <span title={(d.skill_bonus_notes?.[name] || []).join(" / ")}>{tr(name)}</span>
                    <span />
                    <b>{skillDice(rating, d.skill_bonus?.[name])}</b>
                  </div>
                ))}
              </>
            ) : null}
          </div>
        )}

        {tab === "qualities" && (
          <div className="card">
            {d.needs_mentor ? (
              <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
            ) : null}
            <SkillPickSelects
              slots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "quality")}
              tr={tr}
              onPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
            />
            <input type="search" placeholder="クオリティを検索" value={qSearch} onChange={(e) => setQSearch(e.target.value)} />
            <div className="quality-list">
              {filteredQualities.map((q) => {
                const added = ch.quality_ids.includes(q.id);
                const ownedWays = new Set(
                  (catalog.qualities || [])
                    .filter((item) => item.is_way && ch.quality_ids.includes(item.id))
                    .map((item) => item.name),
                );
                const replaces = !added && !!q.is_way && (q.forbidden_qualities || []).some((name) => ownedWays.has(name));
                return (
                  <div className="quality-item" key={q.id}>
                    <div>
                      <b>{tr(q.name)}</b>
                      <div className="muted">
                        {q.name} / {q.category} / カルマ {q.karma} / {q.source}
                        {q.is_way ? " / 他の Way と排他" : ""}
                        {replaces ? " / 追加すると両立しないクオリティを外します" : ""}
                      </div>
                    </div>
                    <button
                      className={`btn ${added ? "danger" : "primary"}`}
                      onClick={() => patch({
                        quality_ids: added ? ch.quality_ids.filter((id) => id !== q.id) : [...ch.quality_ids, q.id],
                        skill_picks: added ? dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]) : (ch.skill_picks || {}),
                      })}
                    >
                      {added ? "削除" : replaces ? "入れ替え" : "追加"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "cyber" && (
          <div className="card">
            <p className="muted">装着中 {d.cyberware?.length || 0} ・ Essence {d.essence}（サイバー −{d.essence_lost_cyber ?? 0}） ・ 消費 {((d.nuyen_spent ?? 0)).toLocaleString()}¥</p>
            {d.limb_replace ? (
              <p className="muted">
                本体 STR {d.limb_replace.str} / AGI {d.limb_replace.agi}
                （リム平均 {d.limb_replace.count}/{d.limb_replace.parts} ・ 肉 STR {d.limb_replace.meat_str} / AGI {d.limb_replace.meat_agi}）
              </p>
            ) : null}
            {d.limb_quality ? <p className="muted">{limbQualityLine(d.limb_quality)}</p> : null}
            <div className="option-row">
              <span>Redliner に含める</span>
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(ch.options?.redliner_torso)}
                  onChange={(e) => patch({
                    options: {
                      redliner_torso: e.target.checked,
                      redliner_skull: Boolean(ch.options?.redliner_skull),
                    },
                  })}
                />
                胴
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(ch.options?.redliner_skull)}
                  onChange={(e) => patch({
                    options: {
                      redliner_torso: Boolean(ch.options?.redliner_torso),
                      redliner_skull: e.target.checked,
                    },
                  })}
                />
                頭蓋
              </label>
            </div>
            {(d.cyberware || []).filter((item) => !item.parent_id).map((item) => (
              <WareRow
                key={item.id}
                item={item}
                childrenItems={(d.cyberware || []).filter((child) => child.parent_id === item.id)}
                catalogItems={catalog.cyberware.items}
                grades={catalog.cyberware.grades}
                kind="cyberware"
                tr={tr}
                slotValue={slotPick[item.id] || ""}
                wareRanges={d.ware_ranges}
                pickSlots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "cyberware")}
                onSkillPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
                onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
                onPatchRow={(id, next) => patch({
                  cyberware: (ch.cyberware || []).map((row) => {
                    if (row.id === id) return { ...row, ...next };
                    if (next.side && row.parent_id === id) return { ...row, side: next.side };
                    return row;
                  }),
                })}
                onRemove={(id) => {
                  const cyberware = removeWareTree(ch.cyberware || [], id);
                  patch({ cyberware, skill_picks: dropRemovedWarePicks(ch.skill_picks, [...cyberware, ...(ch.bioware || [])]) });
                }}
                onAddChild={(wareId) => {
                  const spec = catalog.cyberware.items.find((w) => w.id === wareId);
                  if (!spec) return;
                  const range = wareBounds(spec, d.ware_ranges);
                  patch({
                    cyberware: [
                      ...(ch.cyberware || []),
                      { ware_id: spec.id, rating: range.min, grade: item.grade, wireless: true, parent_id: item.id },
                    ],
                  });
                }}
              />
            ))}
            <div className="cyber-toolbar">
              <input type="search" placeholder="サイバーウェアを検索" value={cySearch} onChange={(e) => setCySearch(e.target.value)} />
              <select value={cyCat} onChange={(e) => setCyCat(e.target.value)}>
                <option value="all">すべての分類</option>
                {cyberCats.map((c) => <option key={c} value={c}>{tr(c)}</option>)}
              </select>
              <select value={addGrade} onChange={(e) => setAddGrade(e.target.value)}>
                {catalog.cyberware.grades.map((g) => (
                  <option key={g.name} value={g.name}>追加時 {g.name}</option>
                ))}
              </select>
            </div>
            <div className="quality-list">
              {filteredCyber.map((w) => (
                <div className="quality-item" key={w.id}>
                  <div>
                    <b>{tr(w.name)}</b>
                    <div className="muted">{w.name} / {w.category} / ESS {w.ess}{w.plugin ? "（単独時）" : ""} / {w.cost}¥ / {w.source}{w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}{w.plugin ? " / スロット可" : ""}</div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => patch({
                      cyberware: [
                        ...(ch.cyberware || []),
                        {
                          ware_id: w.id,
                          rating: w.minrating || 1,
                          grade: addGrade,
                          wireless: true,
                          side: nextFreeSide(ch.cyberware || [], catalog.cyberware.items, w),
                        },
                      ],
                    })}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "bio" && (
          <div className="card">
            <p className="muted">装着中 {d.bioware?.length || 0} ・ Essence {d.essence}（バイオ −{d.essence_lost_bio ?? 0}） ・ 消費 {((d.nuyen_spent ?? 0)).toLocaleString()}¥</p>
            {(d.bioware || []).filter((item) => !item.parent_id).map((item) => (
              <WareRow
                key={item.id}
                item={item}
                childrenItems={(d.bioware || []).filter((child) => child.parent_id === item.id)}
                catalogItems={catalog.bioware.items}
                grades={catalog.bioware.grades}
                kind="bioware"
                tr={tr}
                slotValue={slotPick[item.id] || ""}
                wareRanges={d.ware_ranges}
                pickSlots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "bioware")}
                onSkillPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
                onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
                onPatchRow={(id, next) => patch({
                  bioware: (ch.bioware || []).map((row) => {
                    if (row.id === id) return { ...row, ...next };
                    if (next.side && row.parent_id === id) return { ...row, side: next.side };
                    return row;
                  }),
                })}
                onRemove={(id) => {
                  const bioware = removeWareTree(ch.bioware || [], id);
                  patch({ bioware, skill_picks: dropRemovedWarePicks(ch.skill_picks, [...(ch.cyberware || []), ...bioware]) });
                }}
                onAddChild={(wareId) => {
                  const spec = catalog.bioware.items.find((w) => w.id === wareId);
                  if (!spec) return;
                  const range = wareBounds(spec, d.ware_ranges);
                  patch({
                    bioware: [
                      ...(ch.bioware || []),
                      { ware_id: spec.id, rating: range.min, grade: item.grade, wireless: true, parent_id: item.id },
                    ],
                  });
                }}
              />
            ))}
            <div className="cyber-toolbar">
              <input type="search" placeholder="バイオウェアを検索" value={bioSearch} onChange={(e) => setBioSearch(e.target.value)} />
              <select value={bioCat} onChange={(e) => setBioCat(e.target.value)}>
                <option value="all">すべての分類</option>
                {bioCats.map((c) => <option key={c} value={c}>{tr(c)}</option>)}
              </select>
              <select value={bioGrade} onChange={(e) => setBioGrade(e.target.value)}>
                {catalog.bioware.grades.map((g) => (
                  <option key={g.name} value={g.name}>追加時 {g.name}</option>
                ))}
              </select>
            </div>
            <div className="quality-list">
              {filteredBio.map((w) => (
                <div className="quality-item" key={w.id}>
                  <div>
                    <b>{tr(w.name)}</b>
                    <div className="muted">{w.name} / {w.category} / ESS {w.ess} / {w.cost}¥ / {w.source}{w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}{w.allow_subsystems?.length ? " / スロット可" : ""}</div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => {
                      const range = wareBounds(w, d.ware_ranges);
                      patch({
                        bioware: [
                          ...(ch.bioware || []),
                          {
                            ware_id: w.id,
                            rating: range.min,
                            grade: w.forcegrade || bioGrade,
                            wireless: true,
                            side: nextFreeSide(ch.bioware || [], catalog.bioware.items, w),
                          },
                        ],
                      });
                    }}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "adept" && d.enabled_tabs.includes("adept") && (
          <div className="card">
            <p className="muted">
              パワー点 {formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}
              {(d.way_discount?.max || 0) > 0 ? ` ・ Way割引 ${formatPoints(d.way_discount?.used || 0)}/${formatPoints(d.way_discount?.max || 0)}` : ""}
            </p>
            {d.needs_mentor ? (
              <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
            ) : null}
            {ch.talent === "Mystic Adept" ? (
              <div className="skill-row">
                <span>購入したパワー点（1点=5カルマ）</span>
                <input
                  type="range"
                  min={0}
                  max={d.totals.MAG || 0}
                  value={ch.mystic_pp || 0}
                  onChange={(e) => setCh({ ...ch, mystic_pp: Number(e.target.value) })}
                  onMouseUp={(e) => patch({ mystic_pp: Number((e.target as HTMLInputElement).value) })}
                  onBlur={(e) => patch({ mystic_pp: Number(e.target.value) })}
                />
                <b>{ch.mystic_pp || 0}</b>
              </div>
            ) : null}
            {(d.adept_powers || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name}
                    {item.extra ? `（${item.select === "attribute" ? (ATTR_JA[item.extra] || item.extra) : tr(item.extra)}）` : ""}
                    {" / "}{formatPoints(item.cost)} PP
                    {item.discounted && item.full_cost != null ? `（割引前 ${formatPoints(item.full_cost)}）` : ""}
                    {item.free_levels ? ` / 無料Lv ${item.free_levels}` : ""}
                    {item.total_rating && item.total_rating !== item.rating ? ` / 合計R${item.total_rating}` : ""}
                    {" / "}{item.source}
                    {item.notes?.length ? ` / ${item.notes.join(" ・ ")}` : ""}
                    {item.spell ? ` / ${item.spell.dv} @ F${item.spell.force} → ドレイン ${item.spell.drain == null ? "特殊" : `${item.spell.drain}${item.spell.drain_code || ""}`}（抵抗 ${item.spell.resist_attrs} ${item.spell.resist}）` : ""}
                  </div>
                  <div className="cyber-controls">
                    {!item.free_only && item.rating_max > item.rating_min ? (
                      <label>
                        レーティング
                        <input
                          type="number"
                          min={item.rating_min}
                          max={item.rating_max}
                          value={item.rating}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {!item.free_only ? (
                      <ExtraSelect
                        item={item}
                        tr={tr}
                        onChange={(extra) => patch({
                          adept_powers: (ch.adept_powers || []).map((row) => (
                            row.id === item.id ? { ...row, extra } : row
                          )),
                        })}
                      />
                    ) : null}
                    {item.spell ? (
                      <label>
                        Force
                        <input
                          type="number"
                          min={item.spell.force_min}
                          max={item.spell.force_max}
                          value={item.spell.force}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {item.can_discount ? (
                      <label>
                        <input
                          type="checkbox"
                          checked={!!item.discounted}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, discounted: e.target.checked } : row
                            )),
                          })}
                        />
                        Way割引
                      </label>
                    ) : null}
                  </div>
                </div>
                {item.free_only ? <span className="muted">無料</span> : (
                  <button className="btn danger" onClick={() => patch({
                    adept_powers: (ch.adept_powers || []).filter((row) => row.id !== item.id),
                  })}>削除</button>
                )}
              </div>
            ))}
            <div className="cyber-toolbar" style={{ gridTemplateColumns: "1fr" }}>
              <input type="search" placeholder="アデプトパワーを検索" value={powerSearch} onChange={(e) => setPowerSearch(e.target.value)} />
            </div>
            <div className="quality-list">
              {filteredPowers.map((item) => (
                <div className="quality-item" key={item.id}>
                  <div>
                    <b>{tr(item.name)}</b>
                    <div className="muted">
                      {item.name} / {formatPoints(item.points)} PP{item.extrapointcost ? ` +${formatPoints(item.extrapointcost)}` : ""}
                      {item.adeptway ? ` / Way ${formatPoints(item.adeptway)} 割引` : ""}
                      {item.levels ? " / レベルあり" : ""}
                      {item.select === "spell" ? " / 呪文選択" : ""}
                      {" / "}{item.source}
                    </div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => patch({
                      adept_powers: [...(ch.adept_powers || []), { power_id: item.id, rating: 1, discounted: !!item.adeptway }],
                    })}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
            <h3>Enhancement</h3>
            <p className="muted">Way と対応パワーがあるとき、1つ 2カルマ</p>
            {(d.enhancements || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">{item.name}{item.power ? ` / ${item.power}` : ""} / 2カルマ / {item.source}</div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  adept_enhancements: (ch.adept_enhancements || []).filter((id) => id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="Enhancement を検索" value={enhSearch} onChange={(e) => setEnhSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.enhancements || [])
                .filter((item) => {
                  const q = enhSearch.trim().toLowerCase();
                  return !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                })
                .filter((item) => !(ch.adept_enhancements || []).includes(item.id))
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name}{item.power ? ` / ${item.power}` : ""}
                        {item.required?.quality?.length ? ` / ${item.required.quality.join(" ・ ")}` : ""}
                        {" / 2カルマ / "}{item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      adept_enhancements: [...(ch.adept_enhancements || []), item.id],
                    })}>追加</button>
                  </div>
                ))}
            </div>
            <h3>気焦点</h3>
            <p className="muted">Force × 3,000¥。結合カルマ = Force（Way で減）。Force はパワー点×4</p>
            {(d.qi_foci || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>Qi Focus F{item.rating}</b>
                  <div className="muted">
                    {tr(item.name)}{item.extra ? `（${tr(item.extra)}）` : ""} / R{item.power_rating}
                    {" / "}{item.nuyen.toLocaleString()}¥ / 結合 {item.karma}カルマ
                  </div>
                  <div className="cyber-controls">
                    <label>
                      Force
                      <input
                        type="number"
                        min={item.rating_min}
                        max={item.rating_max}
                        value={item.rating}
                        onChange={(e) => patch({
                          qi_foci: (ch.qi_foci || []).map((row) => (
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    {item.power_rating_max > 1 ? (
                      <label>
                        パワーR
                        <input
                          type="number"
                          min={1}
                          max={item.power_rating_max}
                          value={item.power_rating}
                          onChange={(e) => patch({
                            qi_foci: (ch.qi_foci || []).map((row) => (
                              row.id === item.id ? { ...row, power_rating: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {item.select ? (
                      <label>
                        {selectLabel(item.select)}
                        <select
                          value={item.extra || ""}
                          onChange={(e) => patch({
                            qi_foci: (ch.qi_foci || []).map((row) => (
                              row.id === item.id ? { ...row, extra: e.target.value } : row
                            )),
                          })}
                        >
                          <option value="">選択してください</option>
                          {item.options.map((name) => (
                            <option key={name} value={name}>{item.select === "attribute" ? (ATTR_JA[name] || name) : tr(name)}</option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  qi_foci: (ch.qi_foci || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="気焦点に入れるパワーを検索" value={qiSearch} onChange={(e) => setQiSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.powers || [])
                .filter((item) => {
                  const q = qiSearch.trim().toLowerCase();
                  return q ? item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) : item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={`qi-${item.id}`}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">{item.name} / Force {Math.max(1, Math.ceil((item.points || 0) / 0.25))}〜 / {item.source}</div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      qi_foci: [...(ch.qi_foci || []), { power_id: item.id, rating: Math.max(1, Math.ceil((item.points || 0) / 0.25)), power_rating: 1 }],
                    })}>結合</button>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      <aside className="side">
        <h2>{ch.name}</h2>
        <div className="muted">{tr(ch.metatype)}{ch.metavariant ? ` / ${tr(ch.metavariant)}` : ""} ・ {ch.talent}</div>
        {error ? <p className="errors">{error}</p> : null}
        {d.errors.length ? (
          <ul className="errors">{d.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        ) : (
          <p className="ok">作成ルール上は問題なし</p>
        )}
        {(d.warnings || []).length ? (
          <ul className="warn">{d.warnings!.map((w) => <li key={w}>{w}</li>)}</ul>
        ) : null}
        <div className="stat"><span>物理/精神/社会リミット</span><b>{d.limits.physical}/{d.limits.mental}/{d.limits.social}</b></div>
        <div className="stat"><span>コンディション</span><b>P{d.condition_monitor.physical} / S{d.condition_monitor.stun}</b></div>
        {d.limb_quality ? <div className="stat"><span>リム本数 Quality</span><b>{d.limb_quality.count}本 / {d.limb_quality.pairs}組</b></div> : null}
        <div className="stat"><span>イニシアチブ</span><b>{d.initiative.value}+{d.initiative.dice}d6</b></div>
        <div className="stat"><span>アーマー</span><b>{d.armor}</b></div>
        <div className="stat"><span>エッセンス</span><b>{d.essence}{(d.essence_lost_cyber || d.essence_lost_bio) ? `（C −${d.essence_lost_cyber ?? 0} / B −${d.essence_lost_bio ?? 0}）` : ""}</b></div>
        <div className="stat"><span>ニューエン</span><b>{d.nuyen.toLocaleString()}¥</b></div>
        <div className="stat"><span>カルマ</span><b>{d.karma.remaining} / {d.karma.pool}</b></div>
        <div className="stat"><span>属性点</span><b>{d.points.attributes.used}/{d.points.attributes.max}</b></div>
        <div className="stat"><span>特殊点</span><b>{d.points.special.used}/{d.points.special.max}</b></div>
        <div className="stat"><span>スキル点</span><b>{d.points.skills.used}/{d.points.skills.max}</b></div>
        {d.enabled_tabs.includes("adept") ? (
          <div className="stat"><span>パワー点</span><b>{formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}</b></div>
        ) : null}
        {d.needs_mentor && d.mentor ? <div className="stat"><span>メンター</span><b>{tr(d.mentor.name)}</b></div> : null}
        {(d.damage_resistance || 0) > 0 ? <div className="stat"><span>ダメージ抵抗</span><b>+{d.damage_resistance}</b></div> : null}
        {(d.unarmed_dv || 0) > 0 ? <div className="stat"><span>非武装DV</span><b>+{d.unarmed_dv}</b></div> : null}
        <h3>属性</h3>
        {ATTRS.map((k) => {
          const hidden = (k === "MAG" && !d.enabled_tabs.includes("MAG")) || (k === "RES" && !d.enabled_tabs.includes("RES"));
          if (hidden) return null;
          return (
            <div className="stat" key={k}>
              <span>{ATTR_JA[k]}</span>
              <b>
                {d.totals[k] ?? "-"}
                {d.limb_replace && (k === "STR" || k === "AGI") ? (
                  <span className="muted"> リム平均</span>
                ) : null}
              </b>
            </div>
          );
        })}
        {d.unimplemented_bonuses.length > 0 && (
          <p className="warn">未実装ボーナス {d.unimplemented_bonuses.length} 件（無視して継続）</p>
        )}
      </aside>
    </div>
  );
}
