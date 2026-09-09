import type { Catalog, Character, CharacterSettings } from "./types";
import { type Notice, renderNotice } from "@/lib/engine-notices";
import { readLocale, translate } from "@/lib/i18n";
import * as local from "@/lib/character/local-store";
import { notify } from "@/lib/notices";
import { MessageError } from "@/lib/errors";

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

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(await errorText(res));
  return res.json() as Promise<T>;
}

/** Recompute `derived` for a client-owned state (no merge). */
const computeRemote = (state: Character) =>
  req<Character>("/api/characters/patch", { method: "POST", body: JSON.stringify({ state }) });

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
