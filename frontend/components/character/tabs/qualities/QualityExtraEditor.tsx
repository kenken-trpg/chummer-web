"use client";

import type { Catalog, Character } from "@/lib/types";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

type CatalogQuality = Catalog["qualities"][number];

export function QualityExtraEditor({
  q,
  ch,
  d,
  tr,
  t,
  patch,
  setCharacter,
  catalog,
  catalogById,
}: {
  q: {
    id: string;
    name: string;
    needs_extra?: boolean;
    extra_kind?: string | null;
    select_options?: string[];
    spirit_options?: string[];
    expertise_skill?: string;
    add_spirit_count?: number;
    selectside?: boolean;
  };
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  t: (key: string, fallback?: string) => string;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  setCharacter: (next: Character) => void;
  catalog: Catalog;
  catalogById: Map<string, CatalogQuality>;
}) {
  /**
   * Every control below is one row of the quality list, and its only visible
   * cue is the placeholder option ("対象を選択"). That is not an accessible
   * name, so a character with a dozen qualities that take a target announces
   * a dozen identical comboboxes. Naming each one after its quality
   * ("Allergy: 対象を選択") is what makes the panel navigable.
   */
  const named = (prompt: string) => `${tr(q.name)}: ${prompt}`;

  const kind =
    q.extra_kind ||
    catalogById.get(q.id)?.extra_kind ||
    (q.name === "Exceptional Attribute"
      ? "attribute"
      : q.selectside
        ? "side"
        : q.needs_extra
          ? "text"
          : null);
  const options = q.select_options?.length
    ? q.select_options
    : catalogById.get(q.id)?.select_options || [];
  const addSpiritPicks = (d.add_spirit_picks || []).filter((row) => row.quality_id === q.id);
  if (kind === "add_spirit" || addSpiritPicks.length) {
    const slots = addSpiritPicks.length
      ? addSpiritPicks
      : Array.from(
          {
            length: Math.max(1, q.add_spirit_count || catalogById.get(q.id)?.add_spirit_count || 1),
          },
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
        {slots.map((slot) => {
          const prompt = `追加精霊${slots.length > 1 ? ` ${Number(slot.index) + 1}` : ""}を選択`;
          return (
            <select
              key={slot.key}
              aria-label={named(prompt)}
              value={ch.quality_extras?.[slot.key] || slot.value || ""}
              onChange={(e) =>
                patch({
                  quality_extras: { ...(ch.quality_extras || {}), [slot.key]: e.target.value },
                })
              }
            >
              <option value="">{prompt}</option>
              {(slot.options || []).map((name) => (
                <option key={name} value={name}>
                  {tr(name)}
                </option>
              ))}
            </select>
          );
        })}
      </div>
    );
  }
  if (q.name === "Black Market Pipeline") {
    const contactKey = `${q.id}:contact`;
    return (
      <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <select
          aria-label={named("商品カテゴリを選択")}
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">商品カテゴリを選択</option>
          {["Weapons", "Armor", "Electronics", "Vehicles", "Cyberware", "Bioware", "Drugs"].map(
            (cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ),
          )}
        </select>
        <select
          aria-label={named("コンタクトを選択")}
          value={ch.quality_extras?.[contactKey] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [contactKey]: e.target.value },
            })
          }
        >
          <option value="">コンタクトを選択</option>
          {(d.contacts || []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name || "（無名）"} {c.role ? `／ ${tr(c.role)}` : ""} (C{c.connection}/L
              {c.loyalty})
            </option>
          ))}
        </select>
        {d.black_market_avail_bonus ? (
          <span className="muted">
            入手判定 +{d.black_market_avail_bonus}（実効 Avail −{d.black_market_avail_bonus}）
          </span>
        ) : null}
      </div>
    );
  }
  if (kind === "side" || q.selectside) {
    return (
      <select
        aria-label={named("左右を選択")}
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
          aria-label={named("マトリクスアクションを選択")}
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
          // the catalog list is not exhaustive; "または手入力" alone says
          // nothing about what is being typed
          aria-label={named("マトリクスアクションを手入力")}
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
      : catalog.skills.skills.find((s) => s.name === skillName)?.specs || [];
    return (
      <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <select
          aria-label={named(`${skillName ? `${skillName} の Expertise` : "Expertise"}を選択`)}
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
          aria-label={named("Expertise を手入力")}
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
        aria-label={named("技能を選択")}
        value={current}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">技能を選択</option>
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
            aria-label={named("呪文カテゴリを選択")}
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
            aria-label={named("精霊を選択")}
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
        aria-label={named("付帯資質を選択")}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">付帯資質を選択</option>
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
        aria-label={named("技能グループを選択")}
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
        aria-label={named("能力値を選択")}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">能力値を選択</option>
        {ATTRS.filter((key) => key !== "EDG" && key !== "MAG" && key !== "RES").map((key) => (
          <option key={key} value={key}>
            {attrLabel(key, t)}
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
          aria-label={named("対象")}
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
          aria-label={named("対象を選択")}
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
          aria-label={named("対象を手入力")}
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
