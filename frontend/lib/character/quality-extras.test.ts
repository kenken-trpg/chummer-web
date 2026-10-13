import type { Character } from "@/lib/types";
import { makeCharacter } from "@/tests/fixtures";
import { qualityExtras } from "@/lib/character/quality-extras";

describe("qualityExtras", () => {
  const base = () =>
    makeCharacter({ quality_extras: { allergy: "Pollen", "bmp:contact": "c1" } } as never);

  it("reads a key back, and reads a missing one as empty", () => {
    const extras = qualityExtras(
      base(),
      () => {},
      () => {},
    );
    expect(extras.read("allergy")).toBe("Pollen");
    expect(extras.read("nothing")).toBe("");
  });

  it("keeps the other qualities' choices when one changes", () => {
    // the whole map is sent, so a spread that forgot the rest would wipe
    // every other quality's target
    const sent: Record<string, unknown>[] = [];
    const extras = qualityExtras(
      base(),
      (body) => void sent.push(body),
      () => {},
    );
    extras.commit("allergy", "Sunlight");
    expect(sent).toEqual([{ quality_extras: { allergy: "Sunlight", "bmp:contact": "c1" } }]);
  });

  it("drafts without patching, so typing does not round-trip to the engine", () => {
    const sent: Record<string, unknown>[] = [];
    const drafted: Character[] = [];
    const ch = base();
    const extras = qualityExtras(
      ch,
      (body) => void sent.push(body),
      (next) => void drafted.push(next),
    );
    extras.draft("allergy", "Sunl");
    expect(sent).toEqual([]);
    expect(drafted[0].quality_extras).toEqual({ allergy: "Sunl", "bmp:contact": "c1" });
    // and the character it was given is left alone
    expect(ch.quality_extras?.allergy).toBe("Pollen");
  });
});
