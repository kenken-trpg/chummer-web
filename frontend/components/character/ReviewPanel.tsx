import type { ReactNode } from "react";
import type { Notice } from "@/lib/engine-notices";
import { renderNotice } from "@/lib/engine-notices";
import { useUiText } from "@/lib/i18n";

/** How many notices to list before saying how many more there were. A .chum5
 *  written by a heavily house-ruled Chummer can carry dozens, and a list longer
 *  than the screen is read as a wall rather than as a list. */
const LIST_LIMIT = 20;

/**
 * A list of notices about a file, with whatever answer the caller needs under
 * it.
 *
 * Shared by the two panels that say what a file and this app disagree about:
 * what an export *would* lose, before it is written, and what an import *did*
 * lose, after it was read. Both are the same question asked from either side, so
 * they are worth looking the same — and neither belongs in the red error box,
 * which is for something that failed.
 */
export function ReviewPanel({
  id,
  title,
  notices,
  tr,
  children,
}: {
  id: string;
  title: string;
  notices: Notice[];
  tr: (text: string) => string;
  children: ReactNode;
}) {
  const { ui } = useUiText();
  const shown = notices.slice(0, LIST_LIMIT);
  return (
    <section className="warn export-review" role="alertdialog" aria-labelledby={id}>
      <p id={id}>{title}</p>
      {/* No list at all when there is nothing to list: the export panel now
          opens on unsettled equipment rows alone, and an empty <ul> is read out
          as a list of no items. */}
      {notices.length ? (
        <ul>
          {shown.map((d, i) => (
            <li key={`${d.key}-${i}`}>{renderNotice(d, ui, tr)}</li>
          ))}
          {notices.length > shown.length ? (
            <li className="muted">
              {ui("app.reviewPanel.more", { count: notices.length - shown.length })}
            </li>
          ) : null}
        </ul>
      ) : null}
      {children}
    </section>
  );
}
