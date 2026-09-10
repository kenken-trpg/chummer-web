import type { Catalog, Character, CharacterSettings } from "./types";
import { type Notice, renderNotice } from "@/lib/engine-notices";
import { readLocale, translate } from "@/lib/i18n";
import * as local from "@/lib/character/local-store";
import {
  type CustomDataFiles,
  getCustomData,
  putCustomData,
} from "@/lib/character/customdata-store";
import { notify } from "@/lib/notices";
import { MessageError } from "@/lib/errors";

/** One entry a merge added, removed or edited. */
export type MergeChange = {
  /** The base data file, e.g. `martialarts.xml`. */
  file: string;
  entry: string;
  action: "added" | "removed" | "edited";
  /** Child tags an `edited` rule wrote; empty otherwise. */
  fields: string[];
};

export type MergeResult = {
  dataset: string;
  applied: number;
  skipped: { source: string; reason: string }[];
  changes: MergeChange[];
  /** Set when the itemisation stopped short of `applied`. */
  truncated: boolean;
  /** Base data files the pack edits that this app does not load, e.g.
   *  `critters.xml`. Not a failure — there is nothing to apply them to. */
  ignored: string[];
};

export type CharacterSummary = {
  id: string;
  name: string;
  metatype: string;
  metavariant: string;
  talent: string;
  career: boolean;
  updated: number;
};

/** A `{key, params}` detail, i.e. one our own API raised. FastAPI's own 422
 *  detail is an array, and a plain string is anything else. */
function isNotice(value: unknown): value is Notice {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    typeof (value as Notice).key === "string"
  );
}

/**
 * A user-facing message for a failed response. Our own errors arrive as a
 * `Notice` in `detail` — the wording lives here, in the dictionary, like every
 * other message (docs/i18n.md) — and FastAPI's own validation errors arrive as
 * `{detail: [{msg}, ...]}`. Falls back to the body text, then the status line.
 *
 * `req()` throws a plain `Error`, so this runs outside React and reads the
 * stored locale directly rather than through `useUiText()`.
 */
export async function errorText(res: Response): Promise<string> {
  const raw = await res.text().catch(() => "");
  if (raw && (res.headers.get("content-type") || "").includes("application/json")) {
    try {
      const body = JSON.parse(raw) as { detail?: unknown; message?: unknown };
      const d = body.detail ?? body.message;
      if (isNotice(d)) {
        const locale = readLocale();
        return renderNotice(d, (key, vars) => translate(locale, key, vars));
      }
      if (typeof d === "string") return d;
      if (Array.isArray(d)) {
        const msgs = d
          .map((e) => (e && typeof e === "object" && "msg" in e ? String(e.msg) : String(e)))
          .filter(Boolean);
        if (msgs.length) return msgs.join(" / ");
      }
    } catch {
      /* not JSON after all */
    }
  }
  return raw || res.statusText;
}

/**
 * The dataset the last request was told the server is missing.
 *
 * The custom-data handshake is not a call the UI makes — it is a retry inside
 * `req`. The server answers 409 with the hash it lacks; we upload that set
 * from IndexedDB and repeat the request. Held here rather than passed around
 * because every character request can trigger it and none of them care.
 */
async function reuploadCustomData(res: Response): Promise<boolean> {
  const detail = await res
    .clone()
    .json()
    .then((body: { detail?: Notice }) => body.detail)
    .catch(() => undefined);
  const dataset = String(detail?.params?.dataset ?? "");
  if (!dataset) return false;
  const files = await getCustomData(dataset);
  if (!files) return false;
  // customdata comes back from the character on the retry; the upload only
  // needs the files, and the server re-merges under the same hash.
  await fetch("/api/customdata", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ files, customdata: lastCustomData }),
  });
  return true;
}

/** The enabled-directory list of the character in flight, for the retry. */
let lastCustomData: string[] = [];

/** Remember what the next request's character asks for, so a 409 can rebuild
 *  exactly that set. Called by the character helpers below. */
function noteCustomData(state: Character): void {
  lastCustomData = state.settings?.customdata ?? [];
}

async function req<T>(path: string, init?: RequestInit, retried = false): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (res.status === 409 && !retried && (await reuploadCustomData(res))) {
    return req<T>(path, init, true);
  }
  if (!res.ok) throw new Error(await errorText(res));
  return res.json() as Promise<T>;
}

/** Recompute `derived` for a client-owned state (no merge). */
const computeRemote = (state: Character) => {
  noteCustomData(state);
  return req<Character>("/api/characters/patch", {
    method: "POST",
    body: JSON.stringify({ state }),
  });
};

/**
 * The backend is stateless: it computes and transforms, the browser
 * (IndexedDB, via `local-store`) owns every character. `catalog` is the only
 * call that is still a plain GET; the rest read/write local storage and post
 * the state to the compute service.
 */
export const api = {
  catalog: () => req<Catalog>("/api/catalog"),

  list: () => local.listCharacters(),

  get: async (id: string): Promise<Character> => {
    const stored = await local.getCharacter(id);
    if (!stored) throw new MessageError("app.err.notFound");
    // refresh `derived` against the current engine. The backend being down is
    // survivable — the stored `derived` still renders — but say so, or the
    // sheet quietly shows numbers from a previous engine version.
    const fresh = await computeRemote(stored).catch(() => {
      notify("compute.offline");
      return stored;
    });
    await local.putCharacter(fresh);
    return fresh;
  },

  remove: (id: string) => local.deleteCharacter(id),

  create: async (name = "Runner"): Promise<Character> => {
    const c = await req<Character>("/api/characters/new", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await local.putCharacter(c);
    return c;
  },

  patch: async (id: string, body: Record<string, unknown>): Promise<Character> => {
    const stored = await local.getCharacter(id);
    if (!stored) throw new MessageError("app.err.notFound");
    noteCustomData(stored);
    const next = await req<Character>("/api/characters/patch", {
      method: "POST",
      body: JSON.stringify({ state: stored, patch: body }),
    });
    await local.putCharacter(next);
    return next;
  },

  /** Set a character to `state` verbatim and recompute (undo/redo restore). */
  compute: async (state: Character): Promise<Character> => {
    const next = await computeRemote(state);
    await local.putCharacter(next);
    return next;
  },

  /**
   * Compute a foreign state (a share link, a pasted JSON) for *viewing* only:
   * the backend reissues the id and returns `derived`, and nothing touches the
   * local roster. `import` is this plus the write.
   */
  preview: (payload: unknown): Promise<Character> =>
    req<Character>("/api/characters/import", { method: "POST", body: JSON.stringify(payload) }),

  import: async (payload: unknown): Promise<Character> => {
    const c = await api.preview(payload);
    await local.putCharacter(c);
    return c;
  },

  importChummer: async (
    bytes: ArrayBuffer,
  ): Promise<{ character: Character; warnings: Notice[] }> => {
    const res = await req<{ character: Character; warnings: Notice[] }>(
      "/api/characters/import-chummer",
      { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: bytes },
    );
    await local.putCharacter(res.character);
    return res;
  },

  /**
   * Read a Chummer `settings/*.xml`. The backend owns the parsing — every
   * other piece of Chummer XML knowledge lives there, and deciding which
   * knobs a file changed needs the vendored `settings.xml` to compare with.
   * Nothing is stored server-side; the caller keeps what comes back.
   */
  parseSettings: async (
    bytes: ArrayBuffer,
  ): Promise<{ settings: CharacterSettings; build_method: string | null }> =>
    req<{ settings: CharacterSettings; build_method: string | null }>("/api/settings/parse", {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: bytes,
    }),

  /**
   * Merge a `customdata/` folder and keep the files for the re-upload the
   * server will eventually ask for.
   *
   * The hash comes back from the server rather than being computed here: it
   * is the server's cache key, and one implementation of it is less to keep
   * in step than two.
   */
  uploadCustomData: async (files: CustomDataFiles, customdata: string[]): Promise<MergeResult> => {
    const res = await req<MergeResult>("/api/customdata", {
      method: "POST",
      body: JSON.stringify({ files, customdata }),
    });
    await putCustomData(res.dataset, files);
    return res;
  },

  /** A `.chum5` (plain XML) blob for the given state — caller triggers the download. */
  exportChummer: async (state: Character): Promise<Blob> => {
    const res = await fetch("/api/characters/chummer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state }),
    });
    if (!res.ok) throw new Error(await errorText(res));
    return res.blob();
  },
};
