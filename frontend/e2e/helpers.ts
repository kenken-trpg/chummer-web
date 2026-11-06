import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { deflateRawSync, inflateRawSync } from "node:zlib";
import { expect, type APIRequestContext, type Page } from "@playwright/test";
import type { StoredCharacter } from "../lib/character/local-store";
import type { Character } from "../lib/types";

/** The editor mints a character on first load; wait for the toolbar it fills. */
export async function waitForEditor(page: Page) {
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toBeVisible();
}

/**
 * The conversions (.chum5, .xlsx, FVTT, Cocofolia, Udonarium) live behind the
 * toolbar's 書き出し menu; only the per-session actions are buttons in the row.
 * The menu closes as soon as an item is picked, so one call per item.
 */
export async function openExportMenu(page: Page) {
  await page.getByRole("button", { name: "書き出し ▾" }).click();
}

/**
 * Collect CSP violations. Chromium reports them as console errors, and a
 * blocked script leaves no other trace.
 */
export function watchCsp(page: Page): string[] {
  const violations: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" && /Content Security Policy/i.test(msg.text())) {
      violations.push(msg.text());
    }
  });
  return violations;
}

/**
 * A share fragment value built the way `lib/character/share.ts` builds one:
 * base64url of deflate-raw JSON. Built here rather than through the UI so a
 * test can hand the receiver exactly what an attacker would.
 */
export function encodeFragment(body: unknown): string {
  return deflateRawSync(Buffer.from(JSON.stringify(body))).toString("base64url");
}

export function decodeFragment(value: string): unknown {
  return JSON.parse(inflateRawSync(Buffer.from(value, "base64url")).toString());
}

/** A valid character straight from the engine, without driving the editor. */
export async function freshCharacter(
  request: APIRequestContext,
  name: string,
): Promise<Record<string, unknown>> {
  const res = await request.post("/api/characters/new", { data: { name } });
  expect(res.ok()).toBe(true);
  return res.json();
}

/**
 * The characters in the page's IndexedDB, read directly. For waiting on a
 * write the UI does not announce: an HTTP response can arrive before its
 * record is stored.
 */
export function storedCharacters(page: Page): Promise<Character[]> {
  return page.evaluate(
    () =>
      new Promise((resolve, reject) => {
        const open = indexedDB.open("chummer-web");
        open.onerror = () => reject(open.error);
        open.onsuccess = () => {
          const db = open.result;
          const tx = db.transaction("characters");
          const all: IDBRequest<StoredCharacter[]> = tx.objectStore("characters").getAll();
          // Match the app's persistence boundary: a request event alone is
          // not a committed transaction. Polling must also close its handles.
          tx.oncomplete = () => {
            db.close();
            resolve(all.result.map((r) => r.character));
          };
          tx.onabort = tx.onerror = () => {
            db.close();
            reject(tx.error ?? new Error("Reading stored characters failed"));
          };
        };
      }),
  );
}

/** Read the selected, committed record rather than whichever id sorts first. */
export async function currentCharacter(page: Page): Promise<Character> {
  const id = await page.evaluate(() => localStorage.getItem("lastCharacterId"));
  const character = (await storedCharacters(page)).find((row) => row.id === id);
  if (!character) throw new Error(`Selected character ${id} is not stored yet`);
  return character;
}

/**
 * A save written by Chummer itself, not by this app. The round trip in
 * `character.spec.ts` reads our own writer's output, so both halves can share
 * a misunderstanding; the backend's pytest reads real saves but never through
 * the browser → Next rewrite → body-size guard → IndexedDB path, where a save
 * of several MB (three base64 mugshots) is what actually arrives.
 *
 * Fetched, not committed: it is 5.7 MB of someone else's GPL data. Pinned to a
 * commit and checked by hash, so what runs is exactly what was reviewed.
 */
const FIXTURE = {
  name: "Ghile Mear.chum5",
  commit: "88517555a99e5422e9a215ac88f7e25ecdb69146",
  sha256: "db8f89929b92e2f3a4e6e64e3dcdc905b564f6a640b39ea6b516dc8958dfa853",
};
// gitignored; CI caches it
const CACHE_DIR = join(__dirname, ".fixtures");

export async function chummerFixture(): Promise<string> {
  const path = join(CACHE_DIR, FIXTURE.name);
  const matches = (bytes: Buffer) =>
    createHash("sha256").update(bytes).digest("hex") === FIXTURE.sha256;
  try {
    if (matches(readFileSync(path))) return path;
  } catch {}

  const url =
    `https://raw.githubusercontent.com/chummer5a/chummer5a/${FIXTURE.commit}` +
    `/Chummer.Tests/TestFiles/${encodeURIComponent(FIXTURE.name)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetching ${url}: HTTP ${res.status}`);
  const bytes = Buffer.from(await res.arrayBuffer());
  if (!matches(bytes)) throw new Error(`${FIXTURE.name} does not match its pinned sha256`);
  mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(path, bytes);
  return path;
}
