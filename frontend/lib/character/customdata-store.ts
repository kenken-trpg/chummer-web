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
 * `FileList` from a directory pick -> the settings files and the custom data
 * in it.
 *
 * A published ruleset is distributed as one folder — `settings/` and
 * `customdata/` side by side — so that folder is what the user is asked for,
 * and both halves arrive in one pick. Two shapes have to work:
 *
 * * the whole folder, recognised by a `customdata` path segment. Only what
 *   sits under it becomes custom data, and only `.xml` under a `settings`
 *   segment becomes a settings file; anything else in the tree (`sheets/`,
 *   a readme) is ignored rather than hashed into the dataset.
 * * a bare `customdata/` pick, which has no `settings` half. The picked
 *   folder's own name is dropped and what remains is what a settings file
 *   names.
 *
 * Non-XML files are left out either way: Chummer ignores them too, and they
 * would change the content hash for no reason.
 *
 * Throws when two files land on the same custom-data key. That only happens
 * when the pick carried no directory paths — several `manifest.xml` selected
 * individually rather than the folder — and quietly keeping the last one would
 * merge the wrong custom data while looking like it worked.
 */
export class CustomDataShapeError extends Error {}

export type StyleFolder = {
  /** Settings files found in the pick, in name order. */
  settings: { name: string; text: string }[];
  customdata: CustomDataFiles;
};

/** Index of the last segment equal to `name`, case-insensitively. */
function segment(parts: string[], name: string): number {
  let found = -1;
  parts.forEach((part, i) => {
    if (part.toLowerCase() === name) found = i;
  });
  return found;
}

export async function readStyleFolder(list: FileList): Promise<StyleFolder> {
  const picked = Array.from(list).filter((file) => file.name.toLowerCase().endsWith(".xml"));
  const paths = picked.map((file) => (file.webkitRelativePath || file.name).split("/"));
  // Either half being addressed by name makes this a whole ruleset folder, and
  // then everything in it is addressed by name. Neither means the old bare
  // pick, where the picked folder is `customdata` itself under another name.
  const whole = paths.some(
    (parts) => segment(parts, "customdata") >= 0 || segment(parts, "settings") >= 0,
  );

  const customdata: CustomDataFiles = {};
  const settings: { name: string; text: string }[] = [];
  for (const [i, file] of picked.entries()) {
    const parts = paths[i];
    if (whole) {
      const at = segment(parts, "customdata");
      if (at >= 0) {
        const key = parts.slice(at + 1).join("/");
        if (!key) continue;
        if (key in customdata) throw new CustomDataShapeError(key);
        customdata[key] = await file.text();
      } else if (segment(parts, "settings") >= 0) {
        settings.push({ name: file.name, text: await file.text() });
      }
      continue;
    }
    const key = parts.slice(1).join("/") || file.name;
    if (key in customdata) throw new CustomDataShapeError(key);
    customdata[key] = await file.text();
  }
  settings.sort((a, b) => a.name.localeCompare(b.name));
  return { settings, customdata };
}

/**
 * The folder picked last, so switching rulesets does not ask for it again.
 *
 * Two settings files in one folder usually name different custom-data
 * directories, and the merge is per settings file — but the files themselves
 * are the same pick. Keeping them under a fixed key lets the pulldown re-merge
 * on its own; the per-hash entries above are what a server restart reads back.
 */
const LAST = "folder:last";

export const rememberFolder = (files: CustomDataFiles): Promise<void> => putCustomData(LAST, files);

export async function recallFolder(): Promise<CustomDataFiles | null> {
  const files = await getCustomData(LAST);
  return files && Object.keys(files).length > 0 ? files : null;
}
