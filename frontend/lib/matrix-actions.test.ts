import { expect, it } from "vitest";
import { buildChatPalette } from "@/lib/cocofolia";
import { buildUdonariumPalette } from "@/lib/udonarium";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

it("exports 21 detailed Matrix actions only when enabled, with numeric or variable pools", () => {
  const ch = makeCharacter({
    derived: {
      totals: { LOG: 5, INT: 4, WIL: 3 } as never,
      skill_totals: {
        Cybercombat: 6,
        Hacking: 4,
        Computer: 3,
        Software: 2,
        Hardware: 1,
        "Electronic Warfare": 5,
      },
      skill_bonus: { Software: 1 },
      cyberdeck: { attack: 7, sleaze: 6, dataprocessing: 5, firewall: 4 } as never,
    },
  });
  for (const build of [buildChatPalette, buildUdonariumPalette]) {
    expect(build(ch, makeCatalog(), identityTr)).not.toContain("日本語版 p.");
    const out = build(ch, makeCatalog(), identityTr, "ja", { matrixDetails: true });
    expect(out.split("\n").filter((line) => line.includes("日本語版 p."))).toHaveLength(21);
    expect(out).toContain("強制介入する（複雑動作 / 日本語版 p.239）");
    expect(out).toContain("監視指数を確認する（単純動作 / 日本語版 p.240）");
    expect(out).toContain("マトリックス検索を行う（動作さまざま / 日本語版 p.243）");
    expect(out).toContain("アイコンを追跡する（複雑動作 / 日本語版 p.245）");
  }
  const numeric = buildChatPalette(ch, makeCatalog(), identityTr, "ja", { matrixDetails: true });
  expect(
    numeric
      .split("\n")
      .filter((line) => line.includes("日本語版 p."))
      .map((line) => line.split(" ")[0]),
  ).toEqual([
    "11B6@7",
    "10B6@6",
    "9B6@7",
    "11B6@7",
    "11B6@7",
    "7B6@4",
    "8B6@5",
    "8B6@7",
    "8B6@6",
    "9B6@6",
    "9B6@6",
    "4B6@4",
    "10B6@7",
    "10B6@5",
    "7B6@5",
    "7B6@5",
    "8B6@5",
    "8B6@6",
    "9B6@6",
    "8B6@6",
    "7B6",
  ]);
  expect(numeric).toContain(
    "11B6@7 強制介入する（複雑動作 / 日本語版 p.239） ［Cybercombat6＋LOG5＝11］",
  );
  expect(numeric).toContain(
    "7B6@4 データ爆弾を解除する（複雑動作 / 日本語版 p.240） ［Software2＋INT4＋修正1＝7］",
  );
  const variable = buildUdonariumPalette(ch, makeCatalog(), identityTr, "ja", {
    matrixDetails: true,
  });
  const defs = new Set([...variable.matchAll(/^\/\/(.+?)=/gm)].map((m) => m[1]));
  for (const match of variable.matchAll(/\{([^}]+)\}/g))
    expect(defs.has(match[1]), match[1]).toBe(true);
  expect(variable).toContain("//Software=3");
  expect(variable).toContain("({WIL}+{Hardware}+0)B6@{ファイアウォール}");
  expect(variable).toContain("({INT}+{Computer}+0)B6 アイコンを追跡する");
});

it("includes detailed actions without a deck, and uses ordinary commlink limits", () => {
  for (const build of [buildChatPalette, buildUdonariumPalette]) {
    const bare = makeCharacter();
    const out = build(bare, makeCatalog(), identityTr, "ja", { matrixDetails: true });
    expect(out.split("\n").filter((line) => line.includes("日本語版 p."))).toHaveLength(21);
    expect(build(bare, makeCatalog(), identityTr)).not.toContain("日本語版 p.");
  }
  const link = makeCharacter({
    derived: { commlink: { attack: 0, sleaze: 0, dataprocessing: 3, firewall: 4 } as never },
  });
  const out = buildChatPalette(link, makeCatalog(), identityTr, "ja", { matrixDetails: true });
  expect(out).toMatch(/B6@3 マトリックス知覚を行う/);
  expect(out).toMatch(/B6@4 ジャック・アウトする/);
});

it("shows negative skill modifiers without hiding them in the skill rating", () => {
  const ch = makeCharacter({
    derived: {
      totals: { LOG: 5 } as never,
      skill_totals: { Cybercombat: 6 },
      skill_bonus: { Cybercombat: -2 },
    },
  });
  const out = buildChatPalette(ch, makeCatalog(), identityTr, "ja", { matrixDetails: true });
  expect(out).toContain(
    "9B6@0 強制介入する（複雑動作 / 日本語版 p.239） ［Cybercombat6＋LOG5−修正2＝9］",
  );
});
