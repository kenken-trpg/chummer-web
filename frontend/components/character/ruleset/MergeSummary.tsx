"use client";

import { useState } from "react";
import type { MergeResult } from "@/lib/api";
import { groupChanges } from "@/lib/character/merge-summary";
import type { UiFn } from "@/lib/i18n";

/**
 * What the last custom-data merge did: how much of it applied, what it
 * skipped, and — on request — entry by entry.
 *
 * The breakdown is collapsed by default and its own state, so a new merge
 * arrives collapsed again: the summary line is what a user checks, the table
 * is what someone auditing a pack opens.
 */
export function MergeSummary({ merge, ui }: { merge: MergeResult; ui: UiFn }) {
  const [detail, setDetail] = useState(false);
  return (
    <>
      <p className="muted">
        {ui("settings.customDataApplied", { count: merge.applied })}
        {merge.skipped.length > 0
          ? ` ・ ${ui("settings.customDataSkipped", {
              count: merge.skipped.length,
              items: merge.skipped.map((s) => `${s.source}: ${s.reason}`).join(" / "),
            })}`
          : ""}
        {merge.ignored.length > 0
          ? ` ・ ${ui("settings.customDataIgnored", { files: merge.ignored.join(", ") })}`
          : ""}
        {merge.changes.length > 0 ? (
          <>
            {" ・ "}
            <button className="linklike" onClick={() => setDetail(!detail)} aria-expanded={detail}>
              {ui(detail ? "settings.mergeHide" : "settings.mergeShow")}
            </button>
          </>
        ) : null}
      </p>
      {detail ? <MergeDetail merge={merge} ui={ui} /> : null}
    </>
  );
}

/**
 * What the merge actually did, grouped.
 *
 * The point is to let a table check a pack against what it claims: a group
 * reading "qualities.xml ・ source, page ・ 21" is a re-labelling of entries
 * the app already had, and one reading "martialarts.xml ・ added ・ 57" is new
 * game content. Entry names are listed so the check can go further than the
 * shape.
 */
function MergeDetail({ merge, ui }: { merge: MergeResult; ui: UiFn }) {
  return (
    <div className="merge-detail">
      <table>
        <tbody>
          {groupChanges(merge.changes).map((group) => (
            <tr key={group.key}>
              <td className="merge-file">{group.file}</td>
              <td className="merge-what">
                {group.action === "edited"
                  ? ui("settings.mergeEdited", { fields: group.fields.join(", ") })
                  : ui(group.action === "added" ? "settings.mergeAdded" : "settings.mergeRemoved")}
              </td>
              <td className="merge-count">{ui("settings.mergeCount", { count: group.count })}</td>
              <td className="muted">{group.entries.join("、")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {merge.truncated ? <p className="muted">{ui("settings.mergeTruncated")}</p> : null}
    </div>
  );
}
