import { useEffect, useEffectEvent, useId, useState } from "react";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { selectRoster, type RosterFilter, type RosterSort } from "@/lib/character/roster";
import { useUiText } from "@/lib/i18n";

export function CharacterRoster({ ed }: { ed: CharacterEditor }) {
  const { ui, locale } = useUiText();
  const id = useId();
  const [backingUp, setBackingUp] = useState(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<RosterFilter>("all");
  const [sort, setSort] = useState<RosterSort>("updated");
  const refresh = useEffectEvent(() => {
    void ed.refreshRoster();
  });
  useEffect(() => {
    if (open) refresh();
  }, [open, ed.ch, ed.backupVersion]);
  const rows = selectRoster(ed.roster, query, filter, sort, locale);
  const methodName = (method: string | undefined) => {
    switch (method) {
      case "Priority":
        return ui("prio.method.priority");
      case "SumToTen":
        return ui("prio.method.sumToTen");
      case "Karma":
        return ui("prio.method.karma");
      case "LifeModule":
        return ui("life.method");
      default:
        return method || "—";
    }
  };
  return (
    <section aria-label={ui("app.roster.title")}>
      <button
        className="btn"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(!open)}
      >
        {ui("app.roster.title")}
      </button>
      {open ? (
        <div id={id}>
          <button
            className="btn"
            disabled={backingUp || !ed.roster.length}
            onClick={async () => {
              setBackingUp(true);
              try {
                await ed.downloadAll();
              } finally {
                setBackingUp(false);
              }
            }}
          >
            {ui("app.bulk.download")}
          </button>
          <p className="muted">{ui("app.bulk.entireRoster")}</p>
          <div className="toolbar">
            <label>
              {ui("app.roster.search")}{" "}
              <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} />
            </label>
            <label>
              {ui("app.roster.filter")}{" "}
              <select value={filter} onChange={(e) => setFilter(e.target.value as RosterFilter)}>
                <option value="all">{ui("app.roster.all")}</option>
                <option value="creation">{ui("app.roster.creation")}</option>
                <option value="career">{ui("app.roster.career")}</option>
              </select>
            </label>
            <label>
              {ui("app.roster.sort")}{" "}
              <select value={sort} onChange={(e) => setSort(e.target.value as RosterSort)}>
                <option value="updated">{ui("app.roster.updatedOrder")}</option>
                <option value="name">{ui("app.roster.nameOrder")}</option>
              </select>
            </label>
          </div>
          <p role="status">
            {ui("app.roster.count", { count: rows.length, total: ed.roster.length })}
          </p>
          {!rows.length ? (
            <p>{ui("app.roster.empty")}</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">{ui("toolbar.name")}</th>
                    <th scope="col">{ui("tab.meta")}</th>
                    <th scope="col">{ui("app.roster.method")}</th>
                    <th scope="col">{ui("app.roster.filter")}</th>
                    <th scope="col">{ui("app.roster.updated")}</th>
                    <th scope="col">{ui("app.backup.title")}</th>
                    <th scope="col">{ui("app.roster.action")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <th scope="row">{row.name || ui("toolbar.unnamed")}</th>
                      <td>
                        {ed.tr(row.metatype)}
                        {row.metavariant ? ` / ${ed.tr(row.metavariant)}` : ""}
                      </td>
                      <td>{methodName(row.buildMethod)}</td>
                      <td>{ui(row.career ? "app.roster.career" : "app.roster.creation")}</td>
                      <td>
                        <time dateTime={new Date(row.updated).toISOString()}>
                          {new Date(row.updated).toLocaleString(locale)}
                        </time>
                      </td>
                      <td>
                        {ui(
                          (row.changesSinceBackup ?? 0) > 0
                            ? "app.roster.unbacked"
                            : "app.roster.noChanges",
                        )}
                      </td>
                      <td>
                        <button
                          className="btn"
                          disabled={row.id === ed.ch?.id}
                          onClick={() => void ed.openCharacter(row.id)}
                          aria-label={ui(
                            row.id === ed.ch?.id ? "app.roster.currentName" : "app.roster.openName",
                            { name: row.name || ui("toolbar.unnamed") },
                          )}
                        >
                          {ui(row.id === ed.ch?.id ? "app.roster.current" : "app.roster.open")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
