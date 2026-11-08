import { useMemo, useState } from "react";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import {
  buildSheetSearch,
  searchSheet,
  type SheetSearchTarget,
} from "@/lib/character/sheet-search";
import { useUiText, type MsgKey } from "@/lib/i18n";

export function SheetSearch({
  ed,
  onNavigate,
}: {
  ed: CharacterEditor;
  onNavigate: (target: SheetSearchTarget) => void;
}) {
  const { ui, locale } = useUiText();
  const [query, setQuery] = useState("");
  const entries = useMemo(
    () => (ed.ch && ed.catalog ? buildSheetSearch(ed.ch, ed.catalog, ed.tr, ui) : []),
    [ed.ch, ed.catalog, ed.tr, ui],
  );
  const results = searchSheet(entries, query, locale);
  return (
    <section aria-label={ui("app.sheetSearch.title")}>
      <label>
        {ui("app.sheetSearch.title")}{" "}
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
      </label>
      {query.trim() ? (
        <>
          <p role="status">{ui("app.sheetSearch.count", { count: results.length })}</p>
          {!results.length ? (
            <p>{ui("app.sheetSearch.empty")}</p>
          ) : (
            <ul>
              {results.slice(0, 100).map((entry) => (
                <li key={entry.key}>
                  <button className="btn" onClick={() => onNavigate(entry.target)}>
                    {entry.nickname ? `${entry.nickname} — ` : ""}
                    {entry.name}
                  </button>
                  <span className="muted">
                    {" "}
                    {[
                      ui(`tab.${entry.target.tab}` as MsgKey),
                      entry.target.gearKind
                        ? ui(`gear.kind.${entry.target.gearKind}` as MsgKey)
                        : "",
                      ...entry.path,
                    ]
                      .filter(Boolean)
                      .join(" → ")}
                  </span>
                  {entry.originalName !== entry.name ? (
                    <span className="muted"> / {entry.originalName}</span>
                  ) : null}
                  {entry.notes ? (
                    <details>
                      <summary>{ui("app.sheetSearch.notes")}</summary>
                      <p style={{ whiteSpace: "pre-wrap" }}>{entry.notes}</p>
                    </details>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
          {results.length > 100 ? <p>{ui("app.sheetSearch.limit")}</p> : null}
        </>
      ) : (
        <p className="muted">{ui("app.sheetSearch.hint")}</p>
      )}
    </section>
  );
}
