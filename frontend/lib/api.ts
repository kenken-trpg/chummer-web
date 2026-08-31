import type { Catalog, Character } from "./types";

export type CharacterSummary = {
  id: string;
  name: string;
  metatype: string;
  metavariant: string;
  talent: string;
  career: boolean;
  updated: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  catalog: () => req<Catalog>("/api/catalog"),
  list: () => req<CharacterSummary[]>("/api/characters"),
  get: (id: string) => req<Character>(`/api/characters/${id}`),
  remove: (id: string) => req<{ ok: boolean }>(`/api/characters/${id}`, { method: "DELETE" }),
  create: (name = "Runner") =>
    req<Character>("/api/characters", { method: "POST", body: JSON.stringify({ name }) }),
  patch: (id: string, body: Record<string, unknown>) =>
    req<Character>(`/api/characters/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  import: (payload: unknown) =>
    req<Character>("/api/characters/import", { method: "POST", body: JSON.stringify(payload) }),
  importChummer: (bytes: ArrayBuffer) =>
    req<{ character: Character; warnings: string[] }>("/api/characters/import-chummer", {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: bytes,
    }),
};
