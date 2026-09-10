import { describe, expect, it } from "vitest";
import { priorityTableFor } from "@/lib/character/priority-table";
import { makeCatalog } from "@/tests/fixtures";
import type { Catalog, PriorityCell } from "@/lib/types";

const cell = (name: string, nuyen: number): PriorityCell => ({
  name,
  nuyen,
  metatypes: [],
  talents: [],
});

// Only the two categories these tests read: a full table would be five
// categories of noise, so the partial shape is cast in one place.
function catalogWith(): Catalog {
  return makeCatalog({
    priority_table: {
      Resources: { A: cell("A - 450,000¥", 450000), B: cell("B - 275,000¥", 275000) },
      Heritage: { A: cell("Heritage A", 0) },
    },
    priority_table_overrides: {
      "Prime Runner": { Resources: { A: cell("A - 500,000¥", 500000) } },
    },
  } as unknown as Partial<Catalog>);
}

describe("priorityTableFor", () => {
  it("replaces only the cells the named table overrides", () => {
    const table = priorityTableFor(catalogWith(), "Prime Runner");
    expect(table.Resources.A.nuyen).toBe(500000);
    expect(table.Resources.B.nuyen).toBe(275000);
  });

  it("leaves categories the table says nothing about alone", () => {
    // Prime Runner changes Resources; Heritage stays the shared list rather
    // than being dropped for having no override
    expect(priorityTableFor(catalogWith(), "Prime Runner").Heritage.A.name).toBe("Heritage A");
  });

  it("falls back to the shipped table for a name the data does not have", () => {
    // matches the engine: a settings file naming a table nobody loaded still
    // builds a character
    expect(priorityTableFor(catalogWith(), "Nonexistent").Resources.A.nuyen).toBe(450000);
  });

  it("uses the shipped table when the character named none", () => {
    expect(priorityTableFor(catalogWith(), undefined).Resources.A.nuyen).toBe(450000);
  });
});
