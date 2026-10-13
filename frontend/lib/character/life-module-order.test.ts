import { lifeModuleAppendPatch, lifeModuleOrderPatch } from "./life-modules";
import { makeCharacter } from "@/tests/fixtures";

it("moves acquisition IDs and choice positions together without moving transfers", () => {
  const transfer = {
    id: "t",
    entry_id: "b",
    source_skill_id: "p",
    destination_skill_id: "n",
    grant_fingerprint: "f",
    ranks: 1,
  };
  const ch = makeCharacter({
    life_module_rules_version: 2,
    life_modules: ["first", "second", "third"],
    life_module_entry_ids: ["a", "b", "c"],
    life_module_choices: { "0:q0": "zero", "1:4": "one", "2:3": "two" },
    life_module_transfers: [transfer],
  });
  expect(lifeModuleOrderPatch(ch, [0, 2, 1])).toEqual({
    life_modules: ["first", "third", "second"],
    life_module_entry_ids: ["a", "c", "b"],
    life_module_choices: { "0:q0": "zero", "2:4": "one", "1:3": "two" },
    life_module_transfers: [transfer],
  });
  expect(lifeModuleOrderPatch(ch, [0, 2])).toMatchObject({
    life_module_entry_ids: ["a", "c"],
    life_module_transfers: [],
  });
});

it("gives a newly added acquisition a fresh UUID", () => {
  const ch = makeCharacter({
    life_module_rules_version: 2,
    life_modules: ["first"],
    life_module_entry_ids: ["a"],
  });
  const one = lifeModuleAppendPatch(ch, "second");
  const two = lifeModuleAppendPatch(ch, "second");
  expect(one).toMatchObject({
    life_modules: ["first", "second"],
    life_module_entry_ids: ["a", expect.any(String)],
  });
  expect(one).not.toEqual(two);
});
