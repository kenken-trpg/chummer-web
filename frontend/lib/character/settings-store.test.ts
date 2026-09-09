import { beforeEach, describe, expect, it } from "vitest";
import {
  loadSettingsFiles,
  removeSettingsFile,
  saveSettingsFile,
} from "@/lib/character/settings-store";
import type { CharacterSettings } from "@/lib/types";

const file = (name: string, books: string[] = ["SR5"]): CharacterSettings => ({ name, books });

describe("settings-store", () => {
  beforeEach(() => localStorage.clear());

  it("round-trips a loaded file", () => {
    saveSettingsFile(file("日本_2021_SumTo10", ["SR5", "RG"]));
    expect(loadSettingsFiles()).toEqual([file("日本_2021_SumTo10", ["SR5", "RG"])]);
  });

  it("replaces a file of the same name rather than keeping both", () => {
    // re-importing an edited settings file should update it
    saveSettingsFile(file("House", ["SR5"]));
    const after = saveSettingsFile(file("House", ["SR5", "RG"]));
    expect(after).toEqual([file("House", ["SR5", "RG"])]);
  });

  it("puts the newest first", () => {
    saveSettingsFile(file("A"));
    expect(saveSettingsFile(file("B")).map((f) => f.name)).toEqual(["B", "A"]);
  });

  it("forgets one by name", () => {
    saveSettingsFile(file("A"));
    saveSettingsFile(file("B"));
    expect(removeSettingsFile("A").map((f) => f.name)).toEqual(["B"]);
  });

  it("keeps the entries that still look like settings when the store is junk", () => {
    // hand-edited or written by an older version: salvage, don't wipe
    localStorage.setItem("settingsFiles", JSON.stringify([{ name: "ok", books: [] }, 42, null]));
    expect(loadSettingsFiles()).toEqual([{ name: "ok", books: [] }]);
  });

  it("survives a store holding something that is not a list", () => {
    localStorage.setItem("settingsFiles", '{"nope":true}');
    expect(loadSettingsFiles()).toEqual([]);
    localStorage.setItem("settingsFiles", "not json");
    expect(loadSettingsFiles()).toEqual([]);
  });
});
