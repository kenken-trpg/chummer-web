import { render, screen } from "@testing-library/react";
import { VehiclesSection } from "@/components/character/sheet/sections/Vehicles";
import { textSheet } from "./text-sheet";
import { buildSheetData } from "./sheet-data";
import { buildChatPalette } from "@/lib/cocofolia";
import { buildUdonariumPalette, buildUdonariumVehicles } from "@/lib/udonarium";
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

it("separates a vehicle implant from personal attacks and preserves it in vehicle output and inventory", () => {
  const ch = character(true);
  const blade = ch.derived.weapons![0];
  blade.vehicle_id = "drone";
  ch.derived.drones = [
    {
      id: "drone",
      name: "Doberman",
      body: "4",
      armor: "6",
      pilot: "3",
      sensor: "3",
      handling: "4",
      speed: "3",
      accel: "2",
      category: "Drones: Medium",
    },
    {
      id: "other",
      name: "Other drone",
      body: "4",
      armor: "6",
      pilot: "3",
      sensor: "3",
      handling: "4",
      speed: "3",
      accel: "2",
      category: "Drones: Medium",
    },
  ] as never;
  const catalog = makeCatalog();
  const sheet = buildSheetData({ character: ch, catalog, tr: identityTr, layout: "standard" });
  expect(sheet.weapons.map((row) => row.name)).toEqual(["Ordinary Pistol"]);
  for (const palette of [
    buildChatPalette(ch, catalog, identityTr),
    buildUdonariumPalette(ch, catalog, identityTr),
  ]) {
    expect(palette).not.toContain("Foot Blade");
    expect(palette).toContain("Ordinary Pistol");
  }
  const pieces = buildUdonariumVehicles(ch, catalog, identityTr, "en");
  expect(pieces[0].content).toContain("Implanted weapons: Foot Blade");
  expect(pieces[1].content).not.toContain("Foot Blade");
  // Listing an implant does not invent vehicle Gunnery rolls for it.
  expect(pieces[0].content).not.toContain("//Gunnery=");
  expect(textSheet(sheet)).toContain("内蔵武器: Foot Blade");
  render(<VehiclesSection {...sheet} />);
  expect(screen.getByText("内蔵武器: Foot Blade")).toBeDefined();
  renderWeapons(ch, vi.fn());
  expect(screen.getByText("Foot Blade", { selector: "b" })).toBeDefined();
  expect(screen.getByText("車両内蔵（Doberman）・本人の攻撃候補から除外")).toBeDefined();
  expect(ch.derived.weapons).toHaveLength(2);
});
