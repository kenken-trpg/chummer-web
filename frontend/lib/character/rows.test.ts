import { editRow } from "@/lib/character/rows";

describe("editRow", () => {
  const rows = [
    { id: "a", rating: 1, name: "x" },
    { id: "b", rating: 2, name: "y" },
  ];

  it("changes only the named fields of the row with that id", () => {
    expect(editRow(rows, "b", { rating: 5 })).toEqual([
      { id: "a", rating: 1, name: "x" },
      { id: "b", rating: 5, name: "y" },
    ]);
  });

  it("leaves the input alone and the other rows the same objects", () => {
    const out = editRow(rows, "b", { rating: 5 });
    expect(rows[1].rating).toBe(2);
    expect(out[0]).toBe(rows[0]);
  });

  it("treats a missing list as empty, and an unknown id as no change", () => {
    expect(editRow<(typeof rows)[number]>(undefined, "a", { rating: 3 })).toEqual([]);
    expect(editRow(rows, "zz", { rating: 3 })).toEqual(rows);
  });
});
