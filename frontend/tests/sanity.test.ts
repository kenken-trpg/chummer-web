import { makeCatalog, makeCharacter } from "@/tests/fixtures";

describe("test harness", () => {
  it("runs", () => {
    expect(1 + 1).toBe(2);
  });

  it("builds a typed minimal character + catalog", () => {
    const ch = makeCharacter();
    expect(ch.derived.karma.pool).toBe(25);
    expect(ch.derived.qualities).toEqual([]);
    expect(makeCatalog().skills.groups).toEqual([]);
  });
});
