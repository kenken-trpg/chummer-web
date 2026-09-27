import type { PendingGear } from "@/lib/api";

/**
 * The 装備 rows a キャラシテンプレート import could not match, kept in this
 * browser until someone settles them.
 *
 * They are not part of the character: they are what the *sheet* said, waiting
 * to be turned into items. Keeping them out of `CharacterState` keeps them out
 * of the share link, the .chum5 export and every round-trip that compares one
 * state with another — and losing them costs one re-import of the same file,
 * never a character, which is why `localStorage` is enough (the settings files
 * are kept the same way, and for the same reason).
 */

const KEY = "pendingGear";
/** Enough that importing a few sheets in a row does not drop the first one's
 *  rows, without letting a forgotten character hold the quota for ever. */
const MAX_CHARACTERS = 10;

type Stored = Record<string, PendingGear[]>;

function isRow(value: unknown): value is PendingGear {
  if (typeof value !== "object" || value === null) return false;
  const row = value as PendingGear;
  return typeof row.name === "string" && Array.isArray(row.suggestions);
}

function readAll(): Stored {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return {};
    const out: Stored = {};
    // Written by an older version, or hand-edited: keep the rows that still
    // look like rows rather than throwing the whole store away.
    for (const [id, rows] of Object.entries(parsed as Record<string, unknown>)) {
      if (Array.isArray(rows)) out[id] = rows.filter(isRow);
    }
    return out;
  } catch {
    return {};
  }
}

function writeAll(all: Stored): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(all));
  } catch {
    // A full or disabled store costs the reminder, not the import.
  }
}

export function loadPendingGear(characterId: string): PendingGear[] {
  return readAll()[characterId] ?? [];
}

/** Replaces what is held for `characterId`; an empty list forgets it. */
export function savePendingGear(characterId: string, rows: PendingGear[]): void {
  const { [characterId]: _dropped, ...rest } = readAll();
  if (!rows.length) {
    writeAll(rest);
    return;
  }
  // Newest first, so the cap drops the character imported longest ago.
  const kept = Object.entries(rest).slice(0, MAX_CHARACTERS - 1);
  writeAll({ [characterId]: rows, ...Object.fromEntries(kept) });
}

export function clearPendingGear(characterId: string): void {
  savePendingGear(characterId, []);
}
