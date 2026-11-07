import type { CharacterSummary } from "@/lib/api";
import { notify } from "@/lib/notices";
import type { Character } from "@/lib/types";

/**
 * The character roster lives in the browser (IndexedDB). The backend is a
 * stateless compute/transform service — it never stores a character. Reads
 * degrade to an empty result (private mode, storage disabled, SSR) the same
 * way {@link useSheetLayout} treats localStorage.
 *
 * *Writes* are different: this is the only place a character is kept, so a
 * failed `put` means the work is gone at the next reload. It cannot throw —
 * the in-memory copy in the editor is still good and the session should carry
 * on — so it reports through {@link notify} and returns false instead.
 */

const DB_NAME = "chummer-web";
const STORE = "characters";

/** Bump when a `Character` shape change needs a read-time migration; add the
 *  transform to {@link migrate}. Records written before this field existed
 *  read back as `undefined` and are treated as v0. */
const SCHEMA_VERSION = 2;

export type CharacterSnapshot = { savedAt: number; character: Character };

export type BackupStatus = {
  lastExportedAt: number | null;
  changesSinceBackup: number;
};

export type StoredCharacter = {
  id: string;
  savedAt: number;
  schemaVersion?: number;
  history?: CharacterSnapshot[];
  backup?: BackupStatus;
  character: Character;
};

/** v0 → v1 adds metadata. v1 → v2 life-module normalization runs in the
 *  server engine, which has the catalog and distinguishes creation/career.
 *  Preserve the original inputs here until that recomputation succeeds. */
export function migrate(rec: StoredCharacter): Character {
  return rec.character;
}

let dbPromise: Promise<IDBDatabase> | null = null;

function openDB(): Promise<IDBDatabase> {
  if (typeof indexedDB === "undefined") return Promise.reject(new Error("no indexedDB"));
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) {
          req.result.createObjectStore(STORE, { keyPath: "id" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    // don't cache a failure: a transient open error would otherwise disable
    // storage for the life of the tab
    dbPromise.catch(() => {
      dbPromise = null;
    });
  }
  return dbPromise;
}

function run<T>(
  mode: IDBTransactionMode,
  op: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openDB().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        // Settle on the transaction, not the request: a request's success
        // only means it was queued, and a write is not on disk (or safe from
        // a reload) until the transaction commits. A quota failure also
        // surfaces here, as an abort after the request already "succeeded".
        const tx = db.transaction(STORE, mode);
        const req = op(tx.objectStore(STORE));
        tx.oncomplete = () => resolve(req.result);
        tx.onabort = tx.onerror = () => reject(tx.error ?? req.error);
      }),
  );
}

/**
 * Persist a character. Returns false when the browser refused the write —
 * out of quota (a portrait is megabytes of base64) or storage disabled — and
 * says so through {@link notify}, because the caller's in-memory copy looks
 * saved but will not survive a reload.
 */
export async function putCharacter(character: Character): Promise<boolean> {
  try {
    const db = await openDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      const store = tx.objectStore(STORE);
      const request = store.get(character.id);
      request.onsuccess = () => {
        const previous = request.result as StoredCharacter | undefined;
        const history = previous?.history ?? [];
        // Recomputing on open must not consume an editing-history slot.
        const changed =
          previous && characterInputs(previous.character) !== characterInputs(character);
        const backup = previous?.backup ?? {
          lastExportedAt: null,
          changesSinceBackup: previous?.history?.length ?? 0,
        };
        if (changed) {
          history.push({ savedAt: previous.savedAt, character: previous.character });
        }
        store.put({
          id: character.id,
          savedAt: previous && !changed ? previous.savedAt : Date.now(),
          schemaVersion: SCHEMA_VERSION,
          character,
          history: history.slice(-10),
          backup: { ...backup, changesSinceBackup: backup.changesSinceBackup + (changed ? 1 : 0) },
        });
      };
      tx.oncomplete = () => resolve();
      tx.onabort = tx.onerror = () => reject(tx.error ?? request.error);
    });
    return true;
  } catch (e) {
    // QuotaExceededError is actionable (drop the portrait, delete a character);
    // anything else means storage is simply not available in this context.
    notify(
      e instanceof Error && e.name === "QuotaExceededError" ? "store.quota" : "store.unavailable",
    );
    return false;
  }
}

export async function getCharacter(id: string): Promise<Character | null> {
  try {
    const rec = await run<StoredCharacter | undefined>("readonly", (s) => s.get(id));
    return rec ? migrate(rec) : null;
  } catch {
    return null;
  }
}

export async function deleteCharacter(id: string): Promise<void> {
  try {
    await run("readwrite", (s) => s.delete(id));
  } catch {
    /* nothing to do */
  }
}

export async function listCharacters(): Promise<CharacterSummary[]> {
  try {
    const recs = (await run<StoredCharacter[]>("readonly", (s) => s.getAll())) ?? [];
    return recs
      .map((r) => ({
        id: r.id,
        name: r.character.name,
        metatype: r.character.metatype,
        metavariant: r.character.metavariant ?? "",
        talent: r.character.talent,
        career: Boolean(r.character.career),
        updated: r.savedAt,
        buildMethod: r.character.build_method ?? "Priority",
        changesSinceBackup: r.backup?.changesSinceBackup ?? r.history?.length ?? 0,
      }))
      .sort((a, b) => b.updated - a.updated);
  } catch {
    return [];
  }
}

/** Previous states, newest first; retained with the character across reloads. */
export async function getCharacterSnapshots(id: string): Promise<CharacterSnapshot[]> {
  const rec = await run<StoredCharacter | undefined>("readonly", (s) => s.get(id));
  return (rec?.history ?? []).slice().reverse();
}

function characterInputs({ derived: _derived, ...state }: Character): string {
  void _derived;
  return JSON.stringify(state);
}

/** Export metadata stays local, outside the character and its snapshots. */
export async function getBackupStatus(id: string): Promise<BackupStatus | null> {
  const rec = await run<StoredCharacter | undefined>("readonly", (s) => s.get(id));
  return rec
    ? (rec.backup ?? { lastExportedAt: null, changesSinceBackup: rec.history?.length ?? 0 })
    : null;
}

/** Mark only the state actually offered as JSON. Never overwrite newer edits. */
export async function recordBackup(character: Character): Promise<boolean> {
  const db = await openDB();
  return new Promise<boolean>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    const request = store.get(character.id);
    let recorded = false;
    request.onsuccess = () => {
      const rec = request.result as StoredCharacter | undefined;
      if (!rec) return; // A download finishing after deletion must not recreate it.
      const matches = characterInputs(rec.character) === characterInputs(character);
      rec.backup = {
        lastExportedAt: Date.now(),
        changesSinceBackup: matches
          ? 0
          : Math.max(1, rec.backup?.changesSinceBackup ?? rec.history?.length ?? 0),
      };
      store.put(rec);
      recorded = true;
    };
    tx.oncomplete = () => resolve(recorded);
    tx.onabort = tx.onerror = () => reject(tx.error ?? request.error);
  });
}
