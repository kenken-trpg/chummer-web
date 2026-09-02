import {
  hideFromWareCatalog,
  nextFreeSide,
  removeWareTree,
  sideSlotKey,
  wareBounds,
} from "@/lib/character/ware";
import type { WareCatalogItem, WareInstall } from "@/lib/types";

const inst = (o: Partial<WareInstall>): WareInstall =>
  ({ id: "x", ware_id: "w", rating: 1, grade: "Standard", wireless: true, ...o }) as WareInstall;

const cat = (o: Partial<WareCatalogItem>): WareCatalogItem =>
  ({
    id: "w",
    name: "W",
    category: "C",
    ess: "0",
    cost: "0",
    minrating: 1,
    maxrating: 6,
    plugin: false,
    has_wireless: false,
    source: "SR5",
    page: "0",
    ...o,
  }) as WareCatalogItem;

describe("removeWareTree", () => {
  it("drops the target and every descendant, keeps unrelated rows", () => {
    const items = [
      inst({ id: "arm" }),
      inst({ id: "hand", parent_id: "arm" }),
      inst({ id: "cyberspur", parent_id: "hand" }),
      inst({ id: "eye" }), // unrelated
    ];
    expect(removeWareTree(items, "arm").map((r) => r.id)).toEqual(["eye"]);
  });

  it("is a no-op when the id is absent", () => {
    const items = [inst({ id: "a" }), inst({ id: "b" })];
    expect(removeWareTree(items, "missing")).toHaveLength(2);
  });
});

describe("wareBounds", () => {
  it("prefers a formula-resolved range, else the catalog min/max", () => {
    const item = cat({ id: "w1", minrating: 2, maxrating: 4 });
    expect(wareBounds(item)).toEqual({ min: 2, max: 4 });
    expect(wareBounds(item, { w1: { min: 1, max: 9 } })).toEqual({ min: 1, max: 9 });
    expect(wareBounds(item, { other: { min: 0, max: 0 } })).toEqual({ min: 2, max: 4 });
  });
});

describe("hideFromWareCatalog", () => {
  it("hides plugin-only and formula-rating ware", () => {
    expect(hideFromWareCatalog(cat({ requireparent: true }), "cyberware")).toBe(true);
    expect(hideFromWareCatalog(cat({ formula_rating: true }), "cyberware")).toBe(true);
  });

  it("hides ware that only extends its own kind (an upgrade), not cross-kind", () => {
    expect(hideFromWareCatalog(cat({ required: { cyberware: ["base"] } }), "cyberware")).toBe(true);
    expect(
      hideFromWareCatalog(cat({ required: { cyberware: ["base"], bioware: ["x"] } }), "cyberware"),
    ).toBe(false);
    expect(hideFromWareCatalog(cat({}), "cyberware")).toBe(false);
  });
});

describe("sideSlotKey", () => {
  it("lowercases the limb slot, falling back to the id", () => {
    expect(sideSlotKey(cat({ limbslot: "ARM" }))).toBe("arm");
    expect(sideSlotKey(cat({ id: "Cyberarm", limbslot: null }))).toBe("cyberarm");
  });
});

describe("nextFreeSide", () => {
  const arm = cat({ id: "arm", limbslot: "arm", selectside: true });

  it("returns undefined for non-sided ware", () => {
    expect(nextFreeSide([], [arm], cat({ selectside: false }))).toBeUndefined();
  });

  it("fills Left first, then Right, then wraps to Left when both are taken", () => {
    const withSide = (side: string) => inst({ id: `i-${side}`, ware_id: "arm", side });

    expect(nextFreeSide([], [arm], arm)).toBe("Left");
    expect(nextFreeSide([withSide("Left")], [arm], arm)).toBe("Right");
    expect(nextFreeSide([withSide("Left"), withSide("Right")], [arm], arm)).toBe("Left");
  });

  it("ignores ware in a different limb slot", () => {
    const leg = cat({ id: "leg", limbslot: "leg", selectside: true });
    const usedLeg = inst({ id: "l", ware_id: "leg", side: "Left" });
    expect(nextFreeSide([usedLeg], [arm, leg], arm)).toBe("Left");
  });
});
