"use client";

import type { Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { HelpTip } from "@/components/help/HelpTip";

/**
 * What the qualities so far cost: the karma pool, how much of the negative
 * allowance is spent, and — for a changeling — whether the metagenic halves
 * balance.
 *
 * A career buy-off can take the pool below zero, so this says where that
 * happened rather than leaving a bare negative number in the corner.
 */
export function QualityKarmaSummary({ d, ui }: { d: Character["derived"]; ui: UiFn }) {
  return (
    <>
      <p className={`muted${d.karma.remaining < 0 ? " errors" : ""}`}>
        {ui("common.karmaPool", { remaining: d.karma.remaining, pool: d.karma.pool })}
        {d.karma.remaining < 0
          ? ` ・ ${ui("engine.karma.negative", { karma: d.karma.remaining })}`
          : ""}
        {" ・ "}
        <HelpTip
          label={ui("help.open", { label: ui("qual.negativeKarma", { used: "" }).trim() })}
          lines={[
            { label: ui("help.quality.positive") },
            { label: ui("help.quality.negative") },
            { label: ui("help.quality.career") },
          ]}
        >
          {ui("qual.negativeKarma", { used: d.karma.negative?.used || 0 })}
        </HelpTip>
        {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        {d.career ? ` ・ ${ui("qual.career")}` : ""}
      </p>
      {d.metagenic &&
      (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
        <p className={`muted${d.metagenic.balanced ? "" : " errors"}`}>
          {ui("qual.metagenic", {
            positive: d.metagenic.positive,
            negative: d.metagenic.negative,
          })}
          {d.metagenic.limit > 0
            ? ui("qual.metagenicLimit", { limit: d.metagenic.limit })
            : ui("qual.metagenicNoChangeling")}
          {d.metagenic.balanced ? "" : ui("qual.metagenicUnbalanced")}
        </p>
      ) : null}
    </>
  );
}
