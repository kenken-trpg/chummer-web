import { useState } from "react";
import { api, type PendingGear, type XlsxImport } from "@/lib/api";
import {
  clearPendingGear,
  loadPendingGear,
  savePendingGear,
} from "@/lib/character/pending-gear-store";
import { errorMessage } from "@/lib/errors";
import type { Character } from "@/lib/types";
import { type Notice } from "@/lib/engine-notices";
import type { UiFn } from "@/lib/i18n";

/** A Foundry VTT character actor's Export Data, not this app's own JSON. */
function isFvttActor(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return false;
  const p = payload as Record<string, unknown>;
  return p.type === "character" && typeof p.system === "object" && Array.isArray(p.items);
}

/**
 * Every way a character comes into this app from outside: a dropped file
 * (JSON, .chum5, キャラシテンプレート .xlsx, a Foundry VTT actor) and the same
 * template fetched from its Google Sheets address.
 *
 * Owns the two things an import leaves behind — what the file could not bring
 * over, and the 装備 rows that need a person to say what they are. Opening the
 * imported character is not this hook's job: `remember` and `refreshRoster`
 * come from {@link useCharacterEditor}, which owns the open character.
 */
export function useCharacterImport(opts: {
  ch: Character | null;
  ui: UiFn;
  remember: (c: Character) => void;
  refreshRoster: () => Promise<void>;
  setError: (message: string | null) => void;
  onCharacterOpened?: () => void;
}) {
  const { ch, ui, remember, refreshRoster, setError, onCharacterOpened } = opts;
  /** What the last import could not bring over. Not an error: the character is
   *  open, and this is the list of what to fix by hand. Dropped when the player
   *  closes it, not on the next edit — it is about a file, not about a state. */
  const [importReport, setImportReport] = useState<Notice[] | null>(null);
  /** The 装備 rows of an .xlsx import that need a person to say what they are.
   *  Tied to the character they came from, so switching character shows that
   *  one's rows rather than the wrong sheet's. Kept in this browser (see
   *  `pending-gear-store`) so a reload in the middle of settling twenty rows
   *  does not lose the other nineteen. */
  const [pending, setPendingGear] = useState<{ of: string; rows: PendingGear[] } | null>(null);
  const pendingGear = pending && ch && pending.of === ch.id ? pending.rows : null;

  /** Put what an import lost in front of the player. Empty means nothing was
   *  lost, which is worth saying by showing nothing at all. */
  function reportImport(warnings: Notice[]) {
    setImportReport(warnings.length ? warnings : null);
  }

  function dismissImportReport() {
    setImportReport(null);
  }

  /** Drop a pending row, either because it was added or because it was waved
   *  off. Both are the player saying they are done with it. */
  function resolvePendingGear(name: string) {
    setPendingGear((prev) => {
      if (!prev) return prev;
      const rows = prev.rows.filter((row) => row.name !== name);
      savePendingGear(prev.of, rows);
      return { ...prev, rows };
    });
  }

  function dismissPendingGear() {
    if (pending) clearPendingGear(pending.of);
    setPendingGear(null);
  }

  /** What is held for `id`, so opening a character picks its rows back up. */
  function readPendingGear(id: string) {
    const rows = loadPendingGear(id);
    setPendingGear(rows.length ? { of: id, rows } : null);
  }

  /** What both ways into a キャラシテンプレート do once the sheet has been read:
   *  open it, put its unsettled 装備 rows in front of the player, and say what
   *  the sheet could not be taken at its word on. */
  function openTemplateImport(res: XlsxImport) {
    remember(res.character);
    onCharacterOpened?.();
    savePendingGear(res.character.id, res.pending_gear);
    readPendingGear(res.character.id);
    reportImport(res.warnings);
    void refreshRoster();
  }

  /**
   * Import a キャラシテンプレート from its Google Sheets address.
   *
   * Reported rather than thrown: what usually goes wrong here is that the sheet
   * is not shared, which is something for the player to go and change rather
   * than a fault.
   */
  async function importSheetUrl(url: string) {
    setError(null);
    setImportReport(null);
    try {
      openTemplateImport(await api.importSheetUrl(url));
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.load"));
      throw e;
    }
  }

  async function onImport(file: File) {
    setError(null);
    setImportReport(null);
    try {
      if (/\.xlsx$/i.test(file.name)) {
        openTemplateImport(await api.importXlsx(await file.arrayBuffer()));
        return;
      }
      const payload = /\.chum5(lz)?$/i.test(file.name) ? null : JSON.parse(await file.text());
      if (payload === null || isFvttActor(payload)) {
        const { character, warnings } =
          payload === null
            ? await api.importChummer(await file.arrayBuffer())
            : await api.importFvtt(payload);
        remember(character);
        onCharacterOpened?.();
        reportImport(warnings);
      } else {
        remember(await api.import(payload));
        onCharacterOpened?.();
      }
      void refreshRoster();
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.load"));
    }
  }

  return {
    importReport,
    dismissImportReport,
    importSheetUrl,
    onImport,
    pendingGear,
    readPendingGear,
    resolvePendingGear,
    dismissPendingGear,
  };
}
