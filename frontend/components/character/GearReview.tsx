"use client";

import { useState } from "react";
import type { PendingGear } from "@/lib/api";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { type MsgKey, useUiText } from "@/lib/i18n";

/** Which tab of the gear screen a suggestion would land on, so a shortlist of
 *  names says what each one *is* — a shield is both a weapon and armor. */
const LIST_LABELS: Record<string, MsgKey> = {
  weapons: "gear.kind.weapon",
  weapon_accessories: "gear.kind.weapon",
  armor: "gear.kind.armor",
  armor_mods: "gear.kind.armor",
  commlinks: "gear.kind.commlink",
  cyberdecks: "gear.kind.cyberdeck",
  vehicles: "gear.kind.vehicle",
  drones: "gear.kind.drone",
  lifestyles: "gear.kind.lifestyle",
  gear: "gear.kind.misc",
};

/**
 * The 装備 rows of a キャラシテンプレート import that need a person.
 *
 * That sheet is one free-text column holding weapons, ammunition, armor, drugs,
 * vehicles and lifestyles at once, so a good part of it cannot be matched: a
 * row can be two items in one cell, a name the book does not have, or the
 * player's own shorthand (VI・スチームパンク for the Vashon Island line). Rather
 * than lose those, the import hands each one back with what the sheet said and
 * a shortlist of what it looks like, and this is where they are settled.
 *
 * The suggestions are a shortlist, never a decision: the top one is usually
 * right (アレス・サンダートラック is one syllable out from the catalog's
 * アレス サンダーストラック) but nothing is added until it is clicked.
 */
export function GearReview({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { pendingGear, resolvePendingGear, dismissPendingGear, ch, patch, tr } = ed;
  const [busy, setBusy] = useState<string | null>(null);
  if (!pendingGear || !pendingGear.length || !ch) return null;

  async function add(row: PendingGear, pick: PendingGear["suggestions"][number]) {
    setBusy(row.name);
    try {
      // The import built the row to append, so which lists carry a count,
      // which carry a rating and which count months stays in one place.
      const current = (ch?.[pick.key as keyof typeof ch] as unknown[] | undefined) ?? [];
      await patch({ [pick.key]: [...current, pick.entry] });
      resolvePendingGear(row.name);
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="warn gear-review" aria-labelledby="gear-review-title">
      <p id="gear-review-title">{ui("app.gearReview.title", { count: pendingGear.length })}</p>
      <ul>
        {pendingGear.map((row) => (
          <li key={row.name}>
            <b>{row.name}</b>
            <span className="muted">
              {" "}
              {ui("app.gearReview.row", { qty: row.qty, rating: row.rating })}
              {row.note ? ` / ${row.note}` : ""}
            </span>
            <div className="option-row">
              {row.suggestions.map((pick) => (
                <button
                  key={`${pick.key}-${pick.id}`}
                  className="btn primary"
                  disabled={busy === row.name}
                  onClick={() => void add(row, pick)}
                  title={ui("app.gearReview.addHint", {
                    name: tr(pick.name),
                    list: ui(LIST_LABELS[pick.key] ?? "gear.kind.misc"),
                  })}
                >
                  {tr(pick.name)}
                  <span className="muted"> {ui(LIST_LABELS[pick.key] ?? "gear.kind.misc")}</span>
                </button>
              ))}
              {row.suggestions.length ? null : (
                <span className="muted">{ui("app.gearReview.noneLikeIt")}</span>
              )}
              <button className="btn" onClick={() => resolvePendingGear(row.name)}>
                {ui("app.gearReview.skip")}
              </button>
            </div>
          </li>
        ))}
      </ul>
      <button className="btn" onClick={dismissPendingGear}>
        {ui("app.gearReview.dismiss")}
      </button>
    </section>
  );
}
