import type { Catalog, Character } from "./types";
import * as local from "@/lib/character/local-store";

export type CharacterSummary = {
  id: string;
  name: string;
  metatype: string;
  metavariant: string;
  talent: string;
  career: boolean;
  updated: number;
};

/**
 * A user-facing message for a failed response. FastAPI sends `{detail: "..."}`
 * (or `{detail: [{msg}, ...]}` for 422); pull that out instead of dumping the
 * raw JSON envelope. Falls back to the body text, then the status line.
 */
export async function errorText(res: Response): Promise<string> {
  const raw = await res.text().catch(() => "");
  if (raw && (res.headers.get("content-type") || "").includes("application/json")) {
    try {
      const body = JSON.parse(raw) as { detail?: unknown; message?: unknown };
      const d = body.detail ?? body.message;
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
    if (!stored) throw new Error("キャラクターが見つかりません");
    // refresh `derived` against the current engine; tolerate the backend being down
    const fresh = await computeRemote(stored).catch(() => stored);
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
    if (!stored) throw new Error("キャラクターが見つかりません");
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

  import: async (payload: unknown): Promise<Character> => {
    const c = await req<Character>("/api/characters/import", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await local.putCharacter(c);
    return c;
  },

  importChummer: async (
    bytes: ArrayBuffer,
  ): Promise<{ character: Character; warnings: string[] }> => {
    const res = await req<{ character: Character; warnings: string[] }>(
      "/api/characters/import-chummer",
      { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: bytes },
    );
    await local.putCharacter(res.character);
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
