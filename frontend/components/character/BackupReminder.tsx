import { useEffect, useState } from "react";
import { getBackupStatus, type BackupStatus } from "@/lib/character/local-store";
import { backupDue } from "@/lib/character/backup-reminder";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";

export function BackupReminder({ ed }: { ed: CharacterEditor }) {
  const { ui, locale } = useUiText();
  const [loaded, setLoaded] = useState<{ id: string; status: BackupStatus | null } | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    let active = true;
    const id = ed.ch?.id;
    if (id)
      void getBackupStatus(id)
        .then((status) => {
          if (active) setLoaded({ id, status });
        })
        .catch(() => {
          if (active) setLoaded({ id, status: null });
        });
    return () => {
      active = false;
    };
  }, [ed.ch, ed.backupVersion]);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(timer);
  }, []);
  const status = loaded?.id === ed.ch?.id ? loaded?.status : null;
  const due = status ? backupDue(status, now) : false;
  const button = (
    <button
      className="btn"
      disabled={saving}
      onClick={async () => {
        setSaving(true);
        try {
          await ed.download();
        } finally {
          setSaving(false);
        }
      }}
    >
      {ui("app.backup.download")}
    </button>
  );
  return (
    <div>
      {due ? (
        <div className="notice" role="status">
          <p>{ui("app.backup.reminder", { count: status?.changesSinceBackup ?? 0 })}</p>
          {button}
        </div>
      ) : null}
      <details>
        <summary>{ui("app.backup.title")}</summary>
        <p>{ui("app.backup.description")}</p>
        {status ? (
          <>
            <p>
              {status.lastExportedAt !== null
                ? ui("app.backup.last", {
                    date: new Date(status.lastExportedAt).toLocaleString(locale),
                  })
                : ui("app.backup.never")}
            </p>
            <p>{ui("app.backup.changes", { count: status.changesSinceBackup })}</p>
          </>
        ) : (
          <p>{ui(loaded?.id === ed.ch?.id ? "app.backup.unavailable" : "app.loading")}</p>
        )}
        {!due ? button : null}
      </details>
    </div>
  );
}
