"use client";

import { useMemo, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { MentorPicker } from "@/components/character/MentorPicker";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { ATTRS, ATTR_JA } from "@/lib/character/constants";
import { mergeRatings } from "@/lib/character/format";
import { dropSkillPicksForPrefix, qualityBlockReason, type QualityReqCtx } from "@/lib/character/quality";

export function QualitiesTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const [qSearch, setQSearch] = useState("");
  const [qCat, setQCat] = useState<"all" | "Positive" | "Negative">("all");
  const filteredQualities = useMemo(() => {
    const q = qSearch.trim().toLowerCase();
    return catalog.qualities
      .filter((item) => qCat === "all" || item.category === qCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      })
      .slice(0, 80);
  }, [catalog, qSearch, qCat, tr]);

  const qualityCtx: QualityReqCtx = {
    qualities: new Set((d.qualities || []).map((item) => item.name)),
    metatypes: new Set([ch.metatype, ch.metavariant || ""].filter(Boolean)),
    magenabled: d.enabled_tabs.includes("MAG"),
    resenabled: d.enabled_tabs.includes("RES"),
    skills: mergeRatings(d.skill_totals, d.skillsoft),
    knowledge: mergeRatings(ch.knowledge_skills, d.skillsoft),
    powers: new Set((d.adept_powers || []).map((item) => item.name)),
    spells: new Set((d.spells || []).map((item) => item.name)),
    cyberware: new Set((d.cyberware || []).map((item) => item.name)),
    bioware: new Set((d.bioware || []).map((item) => item.name)),
    tradition: d.tradition?.name || "",
    essence: d.essence,
    essLost: (d.essence_lost_cyber || 0) + (d.essence_lost_bio || 0),
  };
  const ownedFromDerived = d.qualities || [];
  const catalogById = useMemo(() => {
    const map = new Map((catalog.qualities || []).map((item) => [item.id, item]));
    return map;
  }, [catalog.qualities]);

  function renderExtraEditor(q: {
    id: string;
    name: string;
    needs_extra?: boolean;
    extra_kind?: string | null;
    select_options?: string[];
    spirit_options?: string[];
    expertise_skill?: string;
    add_spirit_count?: number;
    selectside?: boolean;
  }) {
    const kind =
      q.extra_kind ||
      catalogById.get(q.id)?.extra_kind ||
      (q.name === "Exceptional Attribute" ? "attribute" : q.selectside ? "side" : q.needs_extra ? "text" : null);
    const options = q.select_options?.length
      ? q.select_options
      : catalogById.get(q.id)?.select_options || [];
    const addSpiritPicks = (d.add_spirit_picks || []).filter((row) => row.quality_id === q.id);
    if (kind === "add_spirit" || addSpiritPicks.length) {
      const slots = addSpiritPicks.length
        ? addSpiritPicks
        : Array.from(
            { length: Math.max(1, q.add_spirit_count || catalogById.get(q.id)?.add_spirit_count || 1) },
            (_, index) => ({
              quality_id: q.id,
              index,
              key: `${q.id}:addspirit:${index}`,
              value: ch.quality_extras?.[`${q.id}:addspirit:${index}`] || "",
              options: (catalog.spirits || [])
                .map((s) => s.name)
                .filter((name) => name && !name.startsWith("Homunculus")),
            }),
          );
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          {slots.map((slot) => (
            <select
              key={slot.key}
              value={ch.quality_extras?.[slot.key] || slot.value || ""}
              onChange={(e) =>
                patch({
                  quality_extras: { ...(ch.quality_extras || {}), [slot.key]: e.target.value },
                })
              }
            >
              <option value="">追加精霊{slots.length > 1 ? ` ${Number(slot.index) + 1}` : ""}を選択</option>
              {(slot.options || []).map((name) => (
                <option key={name} value={name}>
                  {tr(name)}
                </option>
              ))}
            </select>
          ))}
        </div>
      );
    }
    if (q.name === "Black Market Pipeline") {
      const contactKey = `${q.id}:contact`;
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          <select
            value={ch.quality_extras?.[q.id] || ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          >
            <option value="">商品カテゴリを選択</option>
            {["Weapons", "Armor", "Electronics", "Vehicles", "Cyberware", "Bioware", "Drugs"].map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          <select
            value={ch.quality_extras?.[contactKey] || ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [contactKey]: e.target.value },
              })
            }
          >
            <option value="">コネクトを選択</option>
            {(d.contacts || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name || "（無名）"} {c.role ? `／ ${tr(c.role)}` : ""} (C{c.connection}/L{c.loyalty})
              </option>
            ))}
          </select>
          {d.black_market_avail_bonus ? (
            <span className="muted">入手判定 +{d.black_market_avail_bonus}（実効 Avail −{d.black_market_avail_bonus}）</span>
          ) : null}
        </div>
      );
    }
    if (kind === "side" || q.selectside) {
      return (
        <select
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">左右を選択</option>
          <option value="Left">左</option>
          <option value="Right">右</option>
        </select>
      );
    }
    if (kind === "matrix_action") {
      const current = ch.quality_extras?.[q.id] || "";
      const known = options.length ? options : [];
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          <select
            value={known.includes(current) ? current : ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          >
            <option value="">マトリクスアクションを選択</option>
            {known.map((name) => (
              <option key={name} value={name}>
                {tr(name)}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="または手入力"
            value={current}
            onChange={(e) =>
              setCharacter({
                ...ch,
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
            onBlur={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          />
        </div>
      );
    }
    if (kind === "expertise") {
      const current = ch.quality_extras?.[q.id] || "";
      const skillName = q.expertise_skill || catalogById.get(q.id)?.expertise_skill || "";
      const known = options.length
        ? options
        : (catalog.skills.skills.find((s) => s.name === skillName)?.specs || []);
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          <select
            value={known.includes(current) ? current : ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          >
            <option value="">{skillName ? `${skillName} の Expertise` : "Expertise"}を選択</option>
            {known.map((name) => (
              <option key={name} value={name}>
                {tr(name)}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="または手入力"
            value={current}
            onChange={(e) =>
              setCharacter({
                ...ch,
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
            onBlur={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          />
          <span className="muted">専門+3（無料）</span>
        </div>
      );
    }
    if (kind === "weapon_skill") {
      const current = ch.quality_extras?.[q.id] || "";
      const known = options.length ? options : [];
      return (
        <select
          value={current}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">スキルを選択</option>
          {known.map((name) => (
            <option key={name} value={name}>
              {tr(name)}
            </option>
          ))}
        </select>
      );
    }
    if (kind === "spell_category" || kind === "spell_spirit_category" || kind === "spirit_category") {
      const spiritKey = `${q.id}:spiritcategory`;
      const spirits = q.spirit_options?.length
          ? q.spirit_options
          : catalogById.get(q.id)?.spirit_options || [];
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          {kind !== "spirit_category" ? (
            <select
              value={ch.quality_extras?.[q.id] || ""}
              onChange={(e) =>
                patch({
                  quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                })
              }
            >
              <option value="">呪文カテゴリを選択</option>
              {options.map((name) => (
                <option key={name} value={name}>
                  {tr(name)}
                </option>
              ))}
            </select>
          ) : null}
          {kind !== "spell_category" ? (
            <select
              value={ch.quality_extras?.[kind === "spirit_category" ? q.id : spiritKey] || ""}
              onChange={(e) =>
                patch({
                  quality_extras: {
                    ...(ch.quality_extras || {}),
                    [kind === "spirit_category" ? q.id : spiritKey]: e.target.value,
                  },
                })
              }
            >
              <option value="">精霊を選択</option>
              {spirits.map((name) => (
                <option key={name} value={name}>
                  {tr(name)}
                </option>
              ))}
            </select>
          ) : null}
        </div>
      );
    }
    if (kind === "quality") {
      return (
        <select
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">付帯クオリティを選択</option>
          {options.map((name) => (
            <option key={name} value={name}>
              {tr(name)}
            </option>
          ))}
        </select>
      );
    }
    if (kind === "skillgroup") {
      return (
        <select
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">技能グループを選択</option>
          {(catalog.skills.groups || []).map((g) => (
            <option key={g} value={g}>
              {tr(g)}
            </option>
          ))}
        </select>
      );
    }
    if (kind === "attribute" || q.name === "Exceptional Attribute") {
      return (
        <select
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">属性を選択</option>
          {ATTRS.filter((key) => key !== "EDG" && key !== "MAG" && key !== "RES").map((key) => (
            <option key={key} value={key}>
              {ATTR_JA[key] || key}
            </option>
          ))}
        </select>
      );
    }
    if (kind === "text" || q.needs_extra) {
      const current = ch.quality_extras?.[q.id] || "";
      const known = options.length ? options : [];
      if (!known.length) {
        return (
          <input
            type="text"
            placeholder="対象（花粉、日光など）"
            value={current}
            onChange={(e) =>
              setCharacter({
                ...ch,
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
            onBlur={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          />
        );
      }
      return (
        <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
          <select
            value={known.includes(current) ? current : ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          >
            <option value="">対象を選択</option>
            {known.map((name) => (
              <option key={name} value={name}>
                {tr(name)}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="または手入力"
            value={current}
            onChange={(e) =>
              setCharacter({
                ...ch,
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
            onBlur={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          />
        </div>
      );
    }
    return null;
  }

  return (
    <div className="card">
      {d.needs_mentor ? (
        <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
      ) : null}
      <SkillPickSelects
        slots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "quality")}
        tr={tr}
        onPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
      />
      <p className="muted">
        カルマ {d.karma.remaining} / {d.karma.pool}
        {" ・ "}不利から得られるカルマ {d.karma.negative?.used || 0}
        {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        {d.career ? " ・ キャリア" : ""}
      </p>
      {ownedFromDerived.length ? (
        <>
          <h3>取得済み</h3>
          {ownedFromDerived.map((q, idx) => (
            <div className="quality-item" key={`owned-${q.id}-${idx}`}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma}
                  {q.side ? ` / ${q.side === "Left" ? "左" : q.side === "Right" ? "右" : q.side}` : ""}
                  {q.free ? " / 付帯（無料）" : ""}
                </div>
                {renderExtraEditor(q)}
              </div>
              {q.free ? (
                <span className="muted">付帯</span>
              ) : (
                <button
                  className="btn danger"
                  onClick={() => {
                    const extras = { ...(ch.quality_extras || {}) };
                    const remaining = ch.quality_ids.filter((id) => id === q.id).length - 1;
                    if (remaining <= 0) {
                      delete extras[q.id];
                      delete extras[`${q.id}:contact`];
                    }
                    let removed = false;
                    patch({
                      quality_ids: ch.quality_ids.filter((id) => {
                        if (!removed && id === q.id) {
                          removed = true;
                          return false;
                        }
                        return true;
                      }),
                      quality_extras: extras,
                      skill_picks: remaining <= 0
                        ? dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`])
                        : ch.skill_picks,
                    });
                  }}
                >
                  削除
                </button>
              )}
            </div>
          ))}
        </>
      ) : (
        <p className="muted">まだありません。有利／不利で絞り込んで追加できます。</p>
      )}
      <div className="option-row">
        <button className={`tab ${qCat === "all" ? "active" : ""}`} onClick={() => setQCat("all")}>
          すべて
        </button>
        <button className={`tab ${qCat === "Positive" ? "active" : ""}`} onClick={() => setQCat("Positive")}>
          有利
        </button>
        <button className={`tab ${qCat === "Negative" ? "active" : ""}`} onClick={() => setQCat("Negative")}>
          不利
        </button>
      </div>
      <input type="search" placeholder="クオリティを検索" value={qSearch} onChange={(e) => setQSearch(e.target.value)} />
      <div className="quality-list">
        {filteredQualities.map((q) => {
          const ownedCount = ch.quality_ids.filter((id) => id === q.id).length;
          const maxTakes = q.max_takes == null ? null : Number(q.max_takes ?? 1);
          const canAddMore = maxTakes == null || ownedCount < maxTakes;
          const added = ownedCount > 0;
          const ownedWays = new Set(
            (catalog.qualities || [])
              .filter((item) => item.is_way && ch.quality_ids.includes(item.id))
              .map((item) => item.name),
          );
          const replaces = !added && !!q.is_way && (q.forbidden_qualities || []).some((name) => ownedWays.has(name));
          const blocked = canAddMore ? qualityBlockReason(q, qualityCtx) : "";
          return (
            <div className="quality-item" key={q.id}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma} / {q.source}
                  {maxTakes == null ? " / 繰り返し可" : maxTakes > 1 ? ` / 最大${maxTakes}` : ""}
                  {ownedCount > 0 && (maxTakes == null || maxTakes > 1) ? ` / 取得${ownedCount}` : ""}
                  {q.needs_extra ? " / 対象が必要" : ""}
                  {q.is_way ? " / 他の Way と排他" : ""}
                  {replaces ? " / 追加すると両立しないクオリティを外します" : ""}
                  {blocked ? ` / ${blocked}` : ""}
                </div>
              </div>
              <button
                className={`btn ${added && !canAddMore ? "danger" : "primary"}`}
                disabled={canAddMore ? !!blocked : false}
                onClick={() => {
                  if (added && !canAddMore) {
                    const extras = { ...(ch.quality_extras || {}) };
                    delete extras[q.id];
                    delete extras[`${q.id}:contact`];
                    patch({
                      quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                      quality_extras: extras,
                      skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                    });
                    return;
                  }
                  if (!canAddMore || blocked) return;
                  patch({
                    quality_ids: [...ch.quality_ids, q.id],
                    skill_picks: ch.skill_picks || {},
                  });
                }}
              >
                {added && !canAddMore ? "削除" : replaces ? "入れ替え" : "追加"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
