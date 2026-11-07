import type { CharacterSummary } from "@/lib/api";
import { selectRoster } from "./roster";

const rows: CharacterSummary[] = [
  {
    id: "b",
    name: "Runner 10",
    metatype: "Elf",
    metavariant: "",
    talent: "Mundane",
    career: true,
    updated: 20,
  },
  {
    id: "a",
    name: "Ｒｕｎｎｅｒ 2",
    metatype: "Human",
    metavariant: "",
    talent: "Mundane",
    career: false,
    updated: 10,
  },
];

it("combines normalized name search and career filtering", () => {
  expect(selectRoster(rows, " runner ", "creation", "updated", "ja").map((r) => r.id)).toEqual([
    "a",
  ]);
  expect(selectRoster(rows, "runner", "career", "updated", "ja").map((r) => r.id)).toEqual(["b"]);
  expect(selectRoster(rows, "missing", "all", "updated", "ja")).toEqual([]);
});

it("sorts names numerically or by update time without changing the source", () => {
  expect(selectRoster(rows, "", "all", "name", "ja").map((r) => r.id)).toEqual(["a", "b"]);
  expect(selectRoster(rows, "", "all", "updated", "ja").map((r) => r.id)).toEqual(["b", "a"]);
  expect(rows.map((r) => r.id)).toEqual(["b", "a"]);
});
