"use client";

import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

type CatalogQuality = Catalog["qualities"][number];

/**
 * A quality that chooses several attributes, one slot each (Exceptional
 * Attribute chooses one; a metagenic quality may hand out two or three, and
 * each slot can forbid its own).
 *
 * The first slot is stored under the quality's bare id, so a save written
 * before the later slots existed still reads back.
 */
export function AttributeChoiceSlots({
  q,
  ch,
  d,
  t,
  ui,
  patch,
  named,
  choices,
}: {
  q: { id: string; name: string };
  ch: Character;
  d: Character["derived"];
  t: (key: string, fallback?: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  named: (prompt: string) => string;
  choices: NonNullable<CatalogQuality["attribute_choices"]>;
}) {
  const attributeChoices = choices;
  return (
    <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
      {attributeChoices.map((slot, index) => {
        const key = index === 0 ? q.id : `${q.id}:attribute:${index}`;
        // An A.I.'s Depth is not among the open choices: no quality names it.
        const allowed = slot.options.length ? slot.options : ATTRS.filter((k) => k !== "DEP");
        return (
          <label key={key}>
            {ui("quality.attribute")} {index + 1}
            <select
              aria-label={named(`${ui("quality.attribute")} ${index + 1}`)}
              value={ch.quality_extras?.[key] || ""}
              onChange={(e) =>
                patch({ quality_extras: { ...(ch.quality_extras || {}), [key]: e.target.value } })
              }
            >
              <option value="">{ui("quality.attribute")}</option>
              {allowed
                .filter((attr) => attr !== "ESS" && !slot.exclude.includes(attr))
                .filter((attr) => !["MAG", "RES"].includes(attr) || Number(d.totals[attr] || 0) > 0)
                .map((attr) => (
                  <option key={attr} value={attr}>
                    {attrLabel(attr, t)}
                  </option>
                ))}
            </select>
          </label>
        );
      })}
    </div>
  );
}
