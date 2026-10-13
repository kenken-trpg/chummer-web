"use client";

import type { Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";

/** The gear categories Black Market Pipeline can cover (SR5 p.79). */
const MARKET_CATEGORIES = [
  "Weapons",
  "Armor",
  "Electronics",
  "Vehicles",
  "Cyberware",
  "Bioware",
  "Drugs",
];

/**
 * Black Market Pipeline: a gear category, and the contact who supplies it.
 *
 * The contact is a second choice for one quality, so it is stored under
 * `"<id>:contact"` beside the category.
 */
export function BlackMarketPipeline({
  q,
  ch,
  d,
  tr,
  ui,
  patch,
  named,
}: {
  q: { id: string; name: string };
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  named: (prompt: string) => string;
}) {
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
        {MARKET_CATEGORIES.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
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
