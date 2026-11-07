import { useEffect, useState } from "react";
import { getCharacterSnapshots, type CharacterSnapshot } from "@/lib/character/local-store";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";

export function SavedHistory({ ed }: { ed: CharacterEditor }) {
  const { ui, locale } = useUiText();
  const [saved, setSaved] = useState<{ id: string; rows: CharacterSnapshot[] } | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    if (ed.ch) {
      const id = ed.ch.id;
      void getCharacterSnapshots(id)
        .then((rows) => {
          if (active) {
            setSaved({ id, rows });
            setFailed(false);
          }
        })
        .catch(() => {
          if (active) setFailed(true);
        });
    }
    return () => {
      active = false;
    };
  }, [ed.ch]);
  const rows = saved?.id === ed.ch?.id ? (saved?.rows ?? []) : [];
  return (
    <details>
      <summary>{ui("app.savedHistory.title")}</summary>
      <p className="muted">{ui("app.savedHistory.description")}</p>
      {failed ? <p role="alert">{ui("app.savedHistory.failed")}</p> : null}
      {!rows.length ? <p>{ui("app.savedHistory.empty")}</p> : null}
      <ul>
        {rows.map((row, index) => (
          <li key={`${row.savedAt}-${index}`}>
            <time dateTime={new Date(row.savedAt).toISOString()}>
              {new Date(row.savedAt).toLocaleString(locale)}
            </time>
            {" — "}
            {row.character.name}{" "}
            <button
              className="btn"
              disabled={restoring}
              onClick={async () => {
                if (!window.confirm(ui("app.savedHistory.confirm"))) return;
                setRestoring(true);
                try {
                  await ed.restoreSnapshot(row.character, true);
                } finally {
                  setRestoring(false);
                }
              }}
            >
              {ui("app.savedHistory.restore")}
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}
