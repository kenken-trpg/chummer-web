import { exportFilename, exportStamp, safeStem } from "@/lib/character/export-filename";

// A fixed local-time instant, so the assertions do not move with the clock.
const AT = new Date(2026, 9, 3, 19, 12, 30);

describe("exportStamp", () => {
  it("reads as the local date and time, zero-padded", () => {
    expect(exportStamp(AT)).toBe("20261003-191230");
  });

  it("pads every field, so the names of two saves sort chronologically", () => {
    const early = exportStamp(new Date(2026, 0, 2, 3, 4, 5));
    const late = exportStamp(new Date(2026, 10, 20, 13, 40, 50));
    expect(early).toBe("20260102-030405");
    expect([late, early].sort()).toEqual([early, late]);
  });
});

describe("safeStem", () => {
  it("keeps a name a filesystem will take as it is", () => {
    expect(safeStem("Ghile Mear")).toBe("Ghile Mear");
    expect(safeStem("雷電")).toBe("雷電");
  });

  it("replaces the characters Windows forbids rather than dropping them", () => {
    expect(safeStem('A/B\\C:D*E?F"G<H>I|J')).toBe("A_B_C_D_E_F_G_H_I_J");
  });

  it("strips a trailing dot, which Windows drops — gluing the stamp to the extension", () => {
    expect(safeStem("Mr. Johnson.")).toBe("Mr. Johnson");
    expect(safeStem("Fixer ")).toBe("Fixer");
  });

  it("strips control characters instead of turning them into underscores", () => {
    expect(safeStem("Ghile\u0000\tMear")).toBe("GhileMear");
  });

  it("falls back to a name rather than leaving a hidden, nameless file", () => {
    expect(safeStem("")).toBe("character");
    expect(safeStem("   ")).toBe("character");
    expect(safeStem("...")).toBe("character");
  });
});

describe("exportFilename", () => {
  it("carries the character, when it was written, and the format", () => {
    expect(exportFilename("Ghile Mear", "chum5", { at: AT })).toBe(
      "Ghile Mear_20261003-191230.chum5",
    );
    expect(exportFilename("Ghile Mear", "xlsx", { at: AT })).toBe(
      "Ghile Mear_20261003-191230.xlsx",
    );
  });

  it("tells apart the two exports that share an extension", () => {
    expect(exportFilename("Ghile Mear", "json", { at: AT })).toBe(
      "Ghile Mear_20261003-191230.json",
    );
    expect(exportFilename("Ghile Mear", "json", { tag: "fvtt", at: AT })).toBe(
      "Ghile Mear-fvtt_20261003-191230.json",
    );
  });

  it("names an unnamed character rather than writing a bare extension", () => {
    expect(exportFilename("", "chum5", { at: AT })).toBe("character_20261003-191230.chum5");
  });
});
