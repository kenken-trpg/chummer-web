"use client";

import { splitKnobs } from "@/lib/settings-knobs";
import type { UiFn } from "@/lib/i18n";

/**
 * The house-rule knobs this app does not implement, split by whether they
 * matter.
 *
 * The loud ones get a warning rather than a muted aside: they are the knobs
 * whose absence makes a number here disagree with Chummer. The quiet ones are
 * listed because the panel used to print raw tag names that could not be told
 * apart from the loud ones.
 */
export function UnsupportedKnobs({ unsupported, ui }: { unsupported: string[]; ui: UiFn }) {
  const { loud, quiet } = splitKnobs(unsupported, ui);
  return (
    <>
      {loud.length > 0 ? (
        <div className="notice notice-warn">
          {ui("settings.unsupportedHere", { count: loud.length })}
          <ul style={{ margin: "4px 0 0", paddingLeft: "1.2em" }}>
            {loud.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {quiet.length > 0 ? (
        <p className="muted">
          {ui("settings.unsupportedHarmless", { count: quiet.length, items: quiet.join(" / ") })}
        </p>
      ) : null}
    </>
  );
}
