"use client";

import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

type CatalogQuality = Catalog["qualities"][number];

export function QualityExtraEditor({
  q,
  ch,
  d,
  tr,
  t,
  ui,
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
  ui: UiFn;
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
          const prompt =
            slots.length > 1
              ? ui("quality.addSpiritN", { index: Number(slot.index) + 1 })
              : ui("quality.addSpirit");
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
          aria-label={named(ui("quality.marketCategory"))}
          value={ch.quality_extras?.[q.id] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">{ui("quality.marketCategory")}</option>
          {["Weapons", "Armor", "Electronics", "Vehicles", "Cyberware", "Bioware", "Drugs"].map(
            (cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ),
          )}
        </select>
        <select
          aria-label={named(ui("quality.marketContact"))}
          value={ch.quality_extras?.[contactKey] || ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [contactKey]: e.target.value },
            })
          }
        >
          <option value="">{ui("quality.marketContact")}</option>
          {(d.contacts || []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name || ui("common.unnamed")} {c.role ? `／ ${tr(c.role)}` : ""} (C
              {c.connection}/L
              {c.loyalty})
            </option>
          ))}
        </select>
        {d.black_market_avail_bonus ? (
          <span className="muted">
            {ui("quality.marketBonus", { bonus: d.black_market_avail_bonus })}
          </span>
        ) : null}
      </div>
    );
  }
  if (kind === "side" || q.selectside) {
    return (
      <select
        aria-label={named(ui("quality.side"))}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">{ui("quality.side")}</option>
        <option value="Left">{ui("quality.side.left")}</option>
        <option value="Right">{ui("quality.side.right")}</option>
      </select>
    );
  }
  if (kind === "matrix_action") {
    const current = ch.quality_extras?.[q.id] || "";
    const known = options.length ? options : [];
    return (
      <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <select
          aria-label={named(ui("quality.matrixAction"))}
          value={known.includes(current) ? current : ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">{ui("quality.matrixAction")}</option>
          {known.map((name) => (
            <option key={name} value={name}>
              {tr(name)}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder={ui("quality.orType")}
          // the catalog list is not exhaustive; "または手入力" alone says
          // nothing about what is being typed
          aria-label={named(ui("quality.matrixActionFree"))}
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
          aria-label={named(
            skillName ? ui("quality.expertise", { skill: skillName }) : ui("quality.expertiseAny"),
          )}
          value={known.includes(current) ? current : ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">
            {skillName ? ui("quality.expertise", { skill: skillName }) : ui("quality.expertiseAny")}
          </option>
          {known.map((name) => (
            <option key={name} value={name}>
              {tr(name)}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder={ui("quality.orType")}
          aria-label={named(ui("quality.expertiseFree"))}
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
        <span className="muted">{ui("quality.expertiseNote")}</span>
      </div>
    );
  }
  if (kind === "weapon_skill") {
    const current = ch.quality_extras?.[q.id] || "";
    const known = options.length ? options : [];
    return (
      <select
        aria-label={named(ui("quality.weaponSkill"))}
        value={current}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">{ui("quality.weaponSkill")}</option>
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
            aria-label={named(ui("quality.spellCategory"))}
            value={ch.quality_extras?.[q.id] || ""}
            onChange={(e) =>
              patch({
                quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
              })
            }
          >
            <option value="">{ui("quality.spellCategory")}</option>
            {options.map((name) => (
              <option key={name} value={name}>
                {tr(name)}
              </option>
            ))}
          </select>
        ) : null}
        {kind !== "spell_category" ? (
          <select
            aria-label={named(ui("quality.spirit"))}
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
            <option value="">{ui("quality.spirit")}</option>
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
        aria-label={named(ui("quality.attachedQuality"))}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">{ui("quality.attachedQuality")}</option>
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
        aria-label={named(ui("quality.skillGroup"))}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">{ui("quality.skillGroup")}</option>
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
        aria-label={named(ui("quality.attribute"))}
        value={ch.quality_extras?.[q.id] || ""}
        onChange={(e) =>
          patch({
            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
          })
        }
      >
        <option value="">{ui("quality.attribute")}</option>
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
          placeholder={ui("quality.targetPlaceholder")}
          aria-label={named(ui("common.target"))}
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
          aria-label={named(ui("quality.target"))}
          value={known.includes(current) ? current : ""}
          onChange={(e) =>
            patch({
              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
            })
          }
        >
          <option value="">{ui("quality.target")}</option>
          {known.map((name) => (
            <option key={name} value={name}>
              {tr(name)}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder={ui("quality.orType")}
          aria-label={named(ui("quality.targetFree"))}
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
