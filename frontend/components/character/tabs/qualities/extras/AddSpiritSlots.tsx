"use client";

import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";

/**
 * A quality that adds spirits a summoner may call (one or several).
 *
 * The engine lists the slots once the quality is taken; before that — and for
 * a save that predates it — they are synthesised from the catalog's count, so
 * the selects appear immediately rather than after a round trip.
 */
export function AddSpiritSlots({
  q,
  ch,
  d,
  tr,
  ui,
  patch,
  named,
  catalog,
  count,
}: {
  q: { id: string; name: string };
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  named: (prompt: string) => string;
  catalog: Catalog;
  /** How many spirits this quality adds, from the row or the catalog. */
  count: number;
}) {
  const addSpiritPicks = (d.add_spirit_picks || []).filter((row) => row.quality_id === q.id);
  const slots = addSpiritPicks.length
    ? addSpiritPicks
    : Array.from({ length: Math.max(1, count) }, (_, index) => ({
        quality_id: q.id,
        index,
        key: `${q.id}:addspirit:${index}`,
        value: ch.quality_extras?.[`${q.id}:addspirit:${index}`] || "",
        options: (catalog.spirits || [])
          .map((s) => s.name)
          .filter((name) => name && !name.startsWith("Homunculus")),
      }));
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
