import type { Catalog, Character } from "./types";

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
  create: (name = "Runner") => req<Character>("/api/characters", { method: "POST", body: JSON.stringify({ name }) }),
  patch: (id: string, body: Record<string, unknown>) =>
    req<Character>(`/api/characters/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  import: (payload: unknown) => req<Character>("/api/characters/import", { method: "POST", body: JSON.stringify(payload) }),
};
