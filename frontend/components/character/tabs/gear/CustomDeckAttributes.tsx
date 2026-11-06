"use client";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import type { GearCatalogItem } from "@/lib/types";

export const CUSTOM_DECK_ATTRIBUTES = "Custom Cyberdeck Attributes";

const ATTRS = [
  ["Attack", "ATK"],
  ["Sleaze", "SLZ"],
  ["Data Processing", "DP"],
  ["Firewall", "FW"],
] as const;

/** The custom-deck attribute parts that fit the deck `deckName`. */
export function customDeckParts(catalog: TabPanelProps["catalog"], deckName: string) {
  return (catalog.gear || []).filter(
    (row) =>
      row.category === CUSTOM_DECK_ATTRIBUTES && (row.required_names || []).includes(deckName),
  );
}

/**
 * A Fuchi Cyber-N / Cyber-Ex comes at 0 in every attribute; each one is bought
 * on its own (KC p.60), as a part in the deck, at a rating up to the deck's.
 * One select per attribute: 0 is not bought.
 */
export function CustomDeckAttributes({
  deckId,
  deckName,
  deckRating,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  deckId: string;
  deckName: string;
  deckRating: number;
}) {
  const parts = customDeckParts(catalog, deckName);
  if (!parts.length) return null;
  const top = Math.max(1, deckRating);
  const partFor = (attr: string): GearCatalogItem | undefined =>
    parts.find((row) => row.name === `[Custom Cyberdeck] ${attr}`);
  const set = (part: GearCatalogItem, rating: number) => {
    const rest = (ch.gear || []).filter(
      (row) => !(row.parent_id === deckId && row.gear_id === part.id),
    );
    const had = (ch.gear || []).find((row) => row.parent_id === deckId && row.gear_id === part.id);
    patch({
      gear: rating
        ? [...rest, { ...(had || { gear_id: part.id, parent_id: deckId, qty: 1 }), rating }]
        : rest,
    });
  };
  return (
    <div className="matrix-array">
      <HelpTip
        label={ui("help.open", { label: ui("gear.customDeckAttributes") })}
        lines={[{ label: ui("help.gear.customDeckAttributes") }]}
      >
        {ui("gear.customDeckAttributes")}
      </HelpTip>
      {ATTRS.map(([attr, label]) => {
        const part = partFor(attr);
        if (!part) return null;
        const bought = (d.gear || []).find(
          (row) => row.parent_id === deckId && row.gear_id === part.id,
        );
        return (
          <label key={attr}>
            {label}
            <select
              aria-label={`${tr(deckName)}: ${label}`}
              value={String(bought?.rating ?? 0)}
              onChange={(e) => set(part, Number(e.target.value))}
            >
              {Array.from({ length: top + 1 }, (_, n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            {bought ? ` ${bought.nuyen.toLocaleString()}¥` : ""}
          </label>
        );
      })}
    </div>
  );
}
