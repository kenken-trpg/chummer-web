/**
 * The `customdata/` files, kept in this browser.
 *
 * The server holds only what they merge into, under a content hash, and can
 * forget it at any time — so the browser is the durable copy and re-uploads on
 * demand. IndexedDB rather than `localStorage`: a published pack is ~200 KB of
 * XML, which is a large share of the 5 MB `localStorage` budget the settings
 * files already sit in.
 */

const DB = "chummer-customdata";
const STORE = "files";
/** One entry per dataset hash, so two tables' packs can both be present. */
const VERSION = 1;

export type CustomDataFiles = Record<string, string>;

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, VERSION);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error ?? new Error("indexedDB open failed"));
  });
}

function tx<T>(
  mode: IDBTransactionMode,
  run: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return open().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const request = run(db.transaction(STORE, mode).objectStore(STORE));
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error ?? new Error("indexedDB request failed"));
      }),
  );
}

export async function putCustomData(dataset: string, files: CustomDataFiles): Promise<void> {
  try {
    await tx("readwrite", (store) => store.put(files, dataset));
  } catch {
    // A private window or a full quota costs the re-upload convenience, not
    // the character: the server already has this set merged for now.
  }
}

export async function getCustomData(dataset: string): Promise<CustomDataFiles | null> {
  try {
    return (await tx<CustomDataFiles | undefined>("readonly", (s) => s.get(dataset))) ?? null;
  } catch {
    return null;
  }
}

/**
 * `FileList` from a directory pick -> `{path relative to customdata/: text}`.
 *
 * The browser reports paths as `<picked folder>/<rest>`, and the picked folder
 * is `customdata` itself in the normal case — so its own name is dropped and
 * what remains is what a settings file names. Non-XML files are left out:
 * Chummer ignores them too, and they would change the content hash for no
 * reason.
 *
 * Throws when two files land on the same key. That only happens when the pick
 * carried no directory paths — several `manifest.xml` selected individually
 * rather than the folder — and quietly keeping the last one would merge the
 * wrong custom data while looking like it worked.
 */
export class CustomDataShapeError extends Error {}

export async function readCustomDataFolder(list: FileList): Promise<CustomDataFiles> {
  const files: CustomDataFiles = {};
  for (const file of Array.from(list)) {
    if (!file.name.toLowerCase().endsWith(".xml")) continue;
    const full = file.webkitRelativePath || file.name;
    const key = full.split("/").slice(1).join("/") || file.name;
    if (key in files) throw new CustomDataShapeError(key);
    files[key] = await file.text();
  }
  return files;
}
