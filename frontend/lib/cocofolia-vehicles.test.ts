import { buildCocofoliaVehicles } from "@/lib/cocofolia-vehicles";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import type { InstalledDrone, InstalledWeapon, InstalledProgram } from "@/lib/types";

const vehicle = (over: Partial<InstalledDrone> = {}): InstalledDrone => ({
  id: "van",
  gear_id: "van",
  name: "Van",
  category: "Vans",
  handling: "4/2",
  speed: "3",
  accel: "2",
  body: "10",
  armor: "8",
  pilot: "3",
  sensor: "2",
  nuyen: 0,
  ...over,
});
const catalog = makeCatalog({
  skills: {
    groups: [],
    skills: [
      { name: "Pilot Ground Craft", category: "Vehicle Active", attribute: "REA" },
      { name: "Pilot Aircraft", category: "Vehicle Active", attribute: "REA" },
      { name: "Gunnery", category: "Vehicle Active", attribute: "AGI" },
    ],
  } as never,
});
const character = () =>
  makeCharacter({
    derived: {
      totals: { REA: 5, LOG: 6, AGI: 3 } as never,
      skill_totals: { "Pilot Ground Craft": 4, "Pilot Aircraft": 2, Gunnery: 3 },
      skill_bonus: { "Pilot Ground Craft": -1 },
      vehicles: [vehicle({ condition_monitor: 19 })],
      drones: [
        vehicle({ id: "fly", name: "Fly", category: "Drones: Small", body: "0", handling: "3" }),
      ],
    },
  });

describe("Cocofolia vehicle pieces", () => {
  it("returns separate single-piece payloads, with resolved monitors and typed labels", () => {
    const pieces = buildCocofoliaVehicles(character(), catalog, identityTr);
    expect(pieces.map(({ id, kind }) => [id, kind])).toEqual([
      ["van", "vehicles"],
      ["fly", "drones"],
    ]);
    const van = JSON.parse(pieces[0].payload);
    expect(van.kind).toBe("character");
    expect(van.data.name).toBe("Van");
    expect(van.data.status).toEqual([
      { label: "身体CM", value: 19, max: 19 },
      { label: "マトリックスCM", value: 10, max: 10 },
    ]);
    expect(JSON.parse(pieces[1].payload).data.status[0].max).toBe(6);
    expect(van.data.commands).toContain("8B6@4 ヴィークルテスト / Pilot Ground Craft");
    expect(van.data.commands).toContain(
      "9B6@2 ヴィークルテスト（遠隔・ジャンプイン／オフロード） / Pilot Ground Craft",
    );
    expect(van.data.commands).toContain("7B6@4 ヴィークルテスト / Pilot Aircraft");
    expect(van.data.commands).toContain("18B6");
    expect(van.data.memo).toContain("自律テストは未収録");
  });

  it("exports only mounted active guns and only this vehicle's active autosofts", () => {
    const ch = character();
    ch.derived.weapons = [
      {
        id: "gun",
        name: "Gun",
        mounted_on: "van",
        accuracy: "5",
        damage: "10P",
        ap: "-2",
        mode: "FA",
      },
      { name: "Inactive", mounted_on: "van", modular_equipped: false },
      { name: "Other gun", mounted_on: "fly" },
      { name: "Carried gun", vehicle_id: "van" },
    ] as InstalledWeapon[];
    ch.derived.programs = [
      { name: "Maneuvering", rating: 2, category: "Autosofts", parent_id: "van", extra: "Van" },
      { name: "Clearsight", rating: 6, category: "Autosofts", parent_id: "van" },
      { name: "Stopped", rating: 6, category: "Autosofts", parent_id: "van", running: false },
      { name: "Other", rating: 6, category: "Autosofts", parent_id: "fly" },
      { name: "Armor", rating: 6, category: "Common Programs", parent_id: "van" },
    ] as InstalledProgram[];
    const { commands } = JSON.parse(
      buildCocofoliaVehicles(ch, catalog, identityTr)[0].payload,
    ).data;
    expect(commands).toContain("6B6@5 搭載武器 / Gun [DV10P / AP-2 / FA]");
    expect(commands).toContain("9B6@5 搭載武器（遠隔・ジャンプイン） / Gun");
    expect(commands).toContain("5B6@2 自律テスト（搭載オートソフト） / Maneuvering (Van)");
    expect(commands).toContain("9B6@2 自律テスト（搭載オートソフト） / Clearsight");
    for (const excluded of ["Inactive", "Other", "Stopped", "Carried gun", "Armor"])
      expect(commands).not.toContain(excluded);
  });

  it("handles empty ownership, English, and older anthroform monitor data", () => {
    expect(buildCocofoliaVehicles(makeCharacter(), catalog, identityTr)).toEqual([]);
    const ch = character();
    ch.derived.drones = [vehicle({ category: "Drones: Anthro", body: "3" })];
    const piece = JSON.parse(buildCocofoliaVehicles(ch, catalog, identityTr, "en")[1].payload);
    expect(piece.data.status[0].max).toBe(10);
    expect(piece.data.memo).toContain("Choose the Pilot skill");
    expect(piece.data.commands).toContain("Vehicle Test");
  });
});
