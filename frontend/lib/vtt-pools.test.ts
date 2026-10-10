import { vehicleConditionMonitor, vehicleHandling, vehicleSkills } from "@/lib/vtt-pools";
import { makeCatalog } from "@/tests/fixtures";

describe("vehicleHandling", () => {
  it("reads a drone's single number", () => {
    expect(vehicleHandling("3")).toEqual({ onroad: 3, offroad: null });
  });

  it("splits the on-road and off-road pair a vehicle carries", () => {
    expect(vehicleHandling("2/1")).toEqual({ onroad: 2, offroad: 1 });
  });

  it("falls back to zero on a value that is a formula, not a number", () => {
    // the engine writes plain integers, but a stat no mod touched comes
    // through as the catalog has it, and the catalog has "Rating" and "+Rating"
    expect(vehicleHandling("Rating")).toEqual({ onroad: 0, offroad: null });
    expect(vehicleHandling("")).toEqual({ onroad: 0, offroad: null });
  });
});

describe("vehicleConditionMonitor", () => {
  it("is 12 plus half the Body, rounded up (SR5 p.199)", () => {
    expect([0, 1, 6, 15].map(vehicleConditionMonitor)).toEqual([12, 13, 15, 20]);
  });

  it("still gives a microdrone with no Body its 12 boxes", () => {
    expect(vehicleConditionMonitor("")).toBe(12);
  });
});

describe("vehicleSkills", () => {
  it("takes the Pilot skills from the catalog, so a book's extra one is included", () => {
    const catalog = makeCatalog({
      skills: {
        groups: [],
        skills: [
          { id: "1", name: "Pilot Aerospace", attribute: "REA", category: "Vehicle Active" },
          { id: "2", name: "Gunnery", attribute: "AGI", category: "Vehicle Active" },
          { id: "3", name: "Pistols", attribute: "AGI", category: "Combat" },
        ],
      } as never,
    });
    expect(vehicleSkills(catalog)).toEqual({ pilots: ["Pilot Aerospace"], gunnery: "Gunnery" });
  });
});
