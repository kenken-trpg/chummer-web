import { makeCharacter } from "@/tests/fixtures";
import {
  deleteCharacter,
  getCharacter,
  listCharacters,
  migrate,
  putCharacter,
} from "@/lib/character/local-store";

// jsdom ships no IndexedDB. Every accessor must degrade to an empty result
// rather than throw — the editor keeps working from its in-memory copy.
describe("local-store without IndexedDB", () => {
  it("reads resolve empty", async () => {
    expect(await listCharacters()).toEqual([]);
    expect(await getCharacter("nope")).toBeNull();
  });

  it("writes resolve without throwing", async () => {
    await expect(putCharacter(makeCharacter({ id: "x" }))).resolves.toBeUndefined();
    await expect(deleteCharacter("x")).resolves.toBeUndefined();
  });
});

describe("migrate", () => {
  it("passes a v0 record (no schemaVersion) through unchanged", () => {
    const character = makeCharacter({ id: "v0" });
    expect(migrate({ id: "v0", savedAt: 1, character })).toBe(character);
  });
});
