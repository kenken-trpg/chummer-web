import type { CharacterSettings } from "@/lib/types";

/**
 * Settings files the user has loaded, kept in this browser.
 *
 * They are not sent anywhere: `/api/settings/parse` reads a file and hands the
 * result straight back, and the ruleset a character is built under travels
 * inside the character itself. This store only exists so the pulldown still
 * offers a file on the next visit — losing it costs one re-import, never a
 * character, which is why `localStorage` is enough.
 */

const KEY = "settingsFiles";
/** Enough for a table's worth of rulesets without risking the ~5 MB quota
 *  that the characters themselves do not use (those live in IndexedDB). */
const MAX = 50;

export function loadSettingsFiles(): CharacterSettings[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    // Written by an older version, or hand-edited: keep the entries that still
    // look like settings rather than throwing the whole list away.
    return parsed.filter(
      (row): row is CharacterSettings =>
        typeof row === "object" &&
        row !== null &&
        typeof (row as CharacterSettings).name === "string" &&
        Array.isArray((row as CharacterSettings).books),
    );
  } catch {
    return [];
  }
}

/** Adds `entry`, replacing any file of the same name — re-importing an edited
 *  settings file should update it, not leave two entries that differ. */
export function saveSettingsFile(entry: CharacterSettings): CharacterSettings[] {
  const next = [entry, ...loadSettingsFiles().filter((row) => row.name !== entry.name)].slice(
    0,
    MAX,
  );
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // A full or disabled store costs the user the convenience, not the import.
  }
  return next;
}

export function removeSettingsFile(name: string): CharacterSettings[] {
  const next = loadSettingsFiles().filter((row) => row.name !== name);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {}
  return next;
}
