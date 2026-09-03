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
const SCHEMA_VERSION = 1;

export type StoredCharacter = {
  id: string;
  savedAt: number;
  schemaVersion?: number;
  character: Character;
};

/** Upgrade a stored record to the current `Character` shape. v0 → v1 is a
 *  no-op (the field just starts being written); real transforms slot in here
 *  keyed on `rec.schemaVersion`. Exported for unit tests. */
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
        const req = op(db.transaction(STORE, mode).objectStore(STORE));
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
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
    await run("readwrite", (s) =>
      s.put({ id: character.id, savedAt: Date.now(), schemaVersion: SCHEMA_VERSION, character }),
    );
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
      }))
      .sort((a, b) => b.updated - a.updated);
  } catch {
    return [];
  }
}
