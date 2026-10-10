import { screen } from "@testing-library/react";
import { buildSheetData } from "./sheet-data";
import { buildChatPalette } from "@/lib/cocofolia";
import { buildUdonariumPalette } from "@/lib/udonarium";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import {
  owning,
  renderWeapons,
  weapon,
} from "@/components/character/tabs/gear/weapon-gear.helpers";

function character(connected: boolean) {
  return makeCharacter({
    derived: {
      weapons: [
        weapon("blade", "Foot Blade", {
          type: "Melee",
          category: "Cyberweapon",
          from_ware: true,
          source_ware_id: "blade",
          modular_equipped: connected,
        }),
        weapon("gun", "Ordinary Pistol"),
      ] as never,
    },
  });
}

it.each([false, true])(
  "uses connection state %s in the sheet and both chat palettes",
  (connected) => {
    const ch = character(connected);
    const catalog = makeCatalog();
    const sheet = buildSheetData({ character: ch, catalog, tr: identityTr, layout: "standard" });
    expect(sheet.weapons.map((row) => row.name)).toEqual(
      connected ? ["Foot Blade", "Ordinary Pistol"] : ["Ordinary Pistol"],
    );
    for (const palette of [
      buildChatPalette(ch, catalog, identityTr),
      buildUdonariumPalette(ch, catalog, identityTr),
    ]) {
      expect(palette.includes("Foot Blade")).toBe(connected);
      expect(palette).toContain("Ordinary Pistol");
    }
    // Filtering attacks does not discard the inventory rows.
    expect(ch.derived.weapons).toHaveLength(2);
  },
);

it("keeps a detached implanted weapon visible with an inactive label in the equipment editor", () => {
  const blade = weapon("blade", "Foot Blade", {
    from_ware: true,
    source_ware_id: "blade",
    modular_equipped: false,
  });
  renderWeapons(owning([blade]), vi.fn());
  expect(screen.getByText("Foot Blade", { selector: "b" })).toBeDefined();
  expect(screen.getByText("義肢切り離し中・攻撃候補から除外")).toBeDefined();
});
