import { makeCharacter } from "@/tests/fixtures";
import {
  deleteCharacter,
  getCharacter,
  listCharacters,
  migrate,
  putCharacter,
} from "@/lib/character/local-store";
import { onNotice } from "@/lib/notices";

// jsdom ships no IndexedDB. Every accessor must degrade to an empty result
// rather than throw — the editor keeps working from its in-memory copy.
describe("local-store without IndexedDB", () => {
  it("reads resolve empty", async () => {
    expect(await listCharacters()).toEqual([]);
    expect(await getCharacter("nope")).toBeNull();
  });

  it("writes resolve without throwing, but report the failure", async () => {
    const seen: string[] = [];
    onNotice((key) => seen.push(key));

    // false, not a throw: the editor's in-memory copy is still usable
    expect(await putCharacter(makeCharacter({ id: "x" }))).toBe(false);
    expect(seen).toEqual(["store.unavailable"]);
    await expect(deleteCharacter("x")).resolves.toBeUndefined();

    onNotice(null);
  });

  it("names quota exhaustion specifically — it is the actionable one", async () => {
    const seen: string[] = [];
    onNotice((key) => seen.push(key));
    const quota = Object.assign(new Error("full"), { name: "QuotaExceededError" });
    vi.stubGlobal("indexedDB", {
      open: () => {
        throw quota;
      },
    });

    expect(await putCharacter(makeCharacter({ id: "x" }))).toBe(false);
    expect(seen).toEqual(["store.quota"]);

    vi.unstubAllGlobals();
    onNotice(null);
  });
});

describe("migrate", () => {
  it("passes a v0 record (no schemaVersion) through unchanged", () => {
    const character = makeCharacter({ id: "v0" });
    expect(migrate({ id: "v0", savedAt: 1, character })).toBe(character);
  });
});
