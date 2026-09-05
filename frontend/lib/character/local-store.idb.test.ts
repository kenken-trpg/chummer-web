import "fake-indexeddb/auto";

import { makeCharacter } from "@/tests/fixtures";
import {
  deleteCharacter,
  getCharacter,
  listCharacters,
  putCharacter,
  type StoredCharacter,
} from "@/lib/character/local-store";

/**
 * The backend stores nothing, so IndexedDB is the *only* copy of a character.
 * Its sibling `local-store.test.ts` covers the degraded path (jsdom ships no
 * IndexedDB, so every accessor there hits a catch); this file drives a real
 * store, which is where the round trip that users actually depend on lives.
 *
 * `fake-indexeddb/auto` installs the global before `local-store` is imported —
 * that module caches its open request, so the import order matters.
 */

/** Reach past the module's API to plant a record the current code would never
 *  write — an old schema, a shape from a previous release. */
function writeRaw(rec: Record<string, unknown>): Promise<void> {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open("chummer-web", 1);
    open.onsuccess = () => {
      const tx = open.result.transaction("characters", "readwrite");
      tx.objectStore("characters").put(rec);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    };
    open.onerror = () => reject(open.error);
  });
}

beforeEach(async () => {
  for (const row of await listCharacters()) await deleteCharacter(row.id);
});

describe("local-store round trip", () => {
  it("reads back what it wrote", async () => {
    const character = makeCharacter({ id: "a", name: "Jazz" });

    expect(await putCharacter(character)).toBe(true);

    expect(await getCharacter("a")).toEqual(character);
  });

  it("returns null for an id it does not hold", async () => {
    expect(await getCharacter("never-written")).toBeNull();
  });

  it("overwrites in place rather than accumulating revisions", async () => {
    await putCharacter(makeCharacter({ id: "a", name: "Jazz" }));
    await putCharacter(makeCharacter({ id: "a", name: "Jazz the Second" }));

    expect((await getCharacter("a"))?.name).toBe("Jazz the Second");
    expect(await listCharacters()).toHaveLength(1);
  });

  it("forgets a deleted character", async () => {
    await putCharacter(makeCharacter({ id: "a" }));
    await deleteCharacter("a");

    expect(await getCharacter("a")).toBeNull();
    expect(await listCharacters()).toEqual([]);
  });

  it("deleting something absent is not an error", async () => {
    await expect(deleteCharacter("never-written")).resolves.toBeUndefined();
  });
});

describe("listCharacters", () => {
  it("projects the roster summary, most recently saved first", async () => {
    // savedAt is Date.now() at write time and two writes can land in the same
    // millisecond, so pin the clock. Only Date.now, not vi.useFakeTimers():
    // fake-indexeddb delivers its events on real timers and freezing those
    // deadlocks every request made after this test.
    // ids ascend while savedAt does too, so the store's own key order is the
    // *opposite* of the wanted one. Name them the other way round and getAll()
    // happens to return the right answer with no sort at all.
    const now = vi.spyOn(Date, "now").mockReturnValue(1_000);
    await putCharacter(makeCharacter({ id: "a-older", name: "First" }));
    now.mockReturnValue(2_000);
    await putCharacter(
      makeCharacter({ id: "b-newer", name: "Second", metatype: "Elf", talent: "Magician" }),
    );
    now.mockRestore();

    const roster = await listCharacters();

    expect(roster.map((r) => r.id)).toEqual(["b-newer", "a-older"]);
    expect(roster[0]).toEqual({
      id: "b-newer",
      name: "Second",
      metatype: "Elf",
      metavariant: "",
      talent: "Magician",
      career: false,
      updated: 2_000,
    });
  });

  it("carries no `derived` — the roster is a list, not a payload", async () => {
    await putCharacter(makeCharacter({ id: "a" }));

    expect(Object.keys((await listCharacters())[0]).sort()).toEqual([
      "career",
      "id",
      "metatype",
      "metavariant",
      "name",
      "talent",
      "updated",
    ]);
  });
});

describe("reading records written by an older build", () => {
  it("accepts a v0 record, which predates the schemaVersion field", async () => {
    const character = makeCharacter({ id: "v0", name: "Grandfathered" });
    await writeRaw({ id: "v0", savedAt: 1, character });

    expect(await getCharacter("v0")).toEqual(character);
  });

  it("stamps the current schema version on everything it writes", async () => {
    await putCharacter(makeCharacter({ id: "a" }));

    const rec = await new Promise<StoredCharacter>((resolve) => {
      const open = indexedDB.open("chummer-web", 1);
      open.onsuccess = () => {
        const req = open.result.transaction("characters").objectStore("characters").get("a");
        req.onsuccess = () => resolve(req.result as StoredCharacter);
      };
    });

    // if this ever needs changing, `migrate()` needs the matching transform
    expect(rec.schemaVersion).toBe(1);
  });
});
