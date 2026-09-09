import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { saveSettingsFile } from "@/lib/character/settings-store";
import { SettingsPicker } from "@/components/character/SettingsPicker";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

const catalog = makeCatalog({
  books: [
    { code: "SR5", name: "Shadowrun 5th Edition" },
    { code: "RG", name: "Run and Gun" },
    { code: "HT", name: "Hard Targets" },
  ],
  settings_presets: [
    { id: "1", name: "Standard", build_method: "Priority", books: ["SR5"], sum_to_ten: 10 },
    {
      id: "2",
      name: "Sum-to-Ten",
      build_method: "SumToTen",
      books: ["SR5", "RG"],
      sum_to_ten: 10,
    },
  ],
});

function setup(settings?: { name: string; books: string[] }) {
  const patch = vi.fn();
  render(
    <SettingsPicker
      catalog={catalog}
      character={makeCharacter({ settings })}
      ui={testUi}
      tr={identityTr}
      patch={patch}
    />,
  );
  return { patch };
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("SettingsPicker", () => {
  it("starts unrestricted and says so", () => {
    setup();
    expect(screen.getByText("全ルールブックが対象")).toBeDefined();
  });

  it("applies a preset's books and its build method together", () => {
    const { patch } = setup();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Sum-to-Ten" } });
    expect(patch).toHaveBeenCalledWith({
      build_method: "SumToTen",
      settings: { name: "Sum-to-Ten", books: ["SR5", "RG"] },
    });
  });

  it("clears the restriction when the user picks the unrestricted entry", () => {
    const { patch } = setup({ name: "Standard", books: ["SR5"] });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "" } });
    expect(patch).toHaveBeenCalledWith({ settings: { name: "", books: [] } });
  });

  it("drops the preset name once a book is ticked by hand", () => {
    // the character is no longer "Standard"; keeping the name would misreport
    // what it allows
    const { patch } = setup({ name: "Standard", books: ["SR5"] });
    fireEvent.click(screen.getByText("ルールブックを選ぶ"));
    fireEvent.click(screen.getByRole("checkbox", { name: /Hard Targets/ }));
    expect(patch).toHaveBeenCalledWith({ settings: { name: "", books: ["SR5", "HT"] } });
  });

  it("shows a name it does not recognise rather than silently dropping it", () => {
    // an imported .chum5 can name a settings file this app has never seen
    setup({ name: "日本_2021_SumTo10", books: ["SR5", "RG"] });
    expect(screen.getByRole("combobox")).toHaveProperty("value", "");
    expect(screen.getByText(/日本_2021_SumTo10/)).toBeDefined();
  });
});

describe("SettingsPicker with a loaded settings file", () => {
  const house = {
    name: "日本_2021_SumTo10",
    books: ["SR5", "RG"],
    karma_to_nuyen: 3000,
    unsupported: ["ignoreart"],
  };

  it("offers a stored file alongside the shipped presets", () => {
    saveSettingsFile(house);
    setup();
    expect(screen.getByRole("option", { name: "日本_2021_SumTo10" })).toBeDefined();
    expect(screen.getByRole("option", { name: "Standard" })).toBeDefined();
  });

  it("applies the whole file, house-rule numbers included", () => {
    saveSettingsFile(house);
    const { patch } = setup();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: house.name } });
    // no build_method: the stored file carries its own, applied when it was
    // imported, and re-picking it must not reset a method the user changed
    expect(patch).toHaveBeenCalledWith({ settings: house });
  });

  it("names the house rules it cannot honour", () => {
    setup({ ...house });
    expect(screen.getByText(/ignoreart/)).toBeDefined();
  });

  it("keeps the numeric knobs when a book is ticked by hand", () => {
    // only the books and the name are the user's edit here; dropping the karma
    // rate too would silently re-price the character
    const { patch } = setup({ ...house });
    fireEvent.click(screen.getByText("ルールブックを選ぶ"));
    fireEvent.click(screen.getByRole("checkbox", { name: /Hard Targets/ }));
    expect(patch).toHaveBeenCalledWith({
      settings: { ...house, name: "", books: ["SR5", "RG", "HT"] },
    });
  });

  it("imports a file through the API and selects it", async () => {
    const parse = vi
      .spyOn(api, "parseSettings")
      .mockResolvedValue({ settings: house, build_method: "SumToTen" });
    const { patch } = setup();
    const input = screen.getByLabelText("セッティングを読み込む");
    fireEvent.change(input, {
      target: { files: [new File(["<settings/>"], "s.xml", { type: "text/xml" })] },
    });
    await waitFor(() => expect(parse).toHaveBeenCalled());
    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith({ build_method: "SumToTen", settings: house }),
    );
    // and it is remembered for next time
    expect(screen.getByRole("option", { name: house.name })).toBeDefined();
  });

  it("reports a file it could not read instead of failing silently", async () => {
    // the backend's own wording reaches the user; `settings.loadFailed` is
    // only the fallback for a throw that carries no message
    vi.spyOn(api, "parseSettings").mockRejectedValue(
      new Error("このファイルは Chummer のセッティングファイルとして読めませんでした。"),
    );
    setup();
    fireEvent.change(screen.getByLabelText("セッティングを読み込む"), {
      target: { files: [new File(["nope"], "s.xml")] },
    });
    await waitFor(() => expect(screen.getByText(/読めませんでした/)).toBeDefined());
  });

  it("falls back to its own wording when the throw carries no message", async () => {
    vi.spyOn(api, "parseSettings").mockRejectedValue(new Error(""));
    setup();
    fireEvent.change(screen.getByLabelText("セッティングを読み込む"), {
      target: { files: [new File(["nope"], "s.xml")] },
    });
    await waitFor(() =>
      expect(screen.getByText("セッティングファイルを読み込めませんでした。")).toBeDefined(),
    );
  });
});

describe("SettingsPicker with custom data", () => {
  const withCustom = {
    name: "新東京スタイル2024_SumTo10",
    books: ["SR5", "RG"],
    customdata: ["a>1", "b>1"],
  };

  it("says the ruleset is incomplete until the folder is loaded", () => {
    // a settings file naming custom data is unusable without it: everything
    // those directories add is simply missing
    setup(withCustom);
    expect(screen.getByText(/カスタムデータを参照しています/)).toBeDefined();
  });

  it("offers no custom-data button for a ruleset that needs none", () => {
    setup({ name: "Standard", books: ["SR5"] });
    expect(screen.queryByText(/カスタムデータを読み込む/)).toBeNull();
  });

  it("uploads the folder and stores the hash on the character", async () => {
    const upload = vi
      .spyOn(api, "uploadCustomData")
      .mockResolvedValue({ dataset: "abc123", applied: 217, skipped: [] });
    const { patch } = setup(withCustom);
    const input = screen.getByLabelText("カスタムデータを読み込む（2 件必要）");
    const file = new File(["<chummer/>"], "custom_x.xml", { type: "text/xml" });
    Object.defineProperty(file, "webkitRelativePath", { value: "customdata/d/custom_x.xml" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() =>
      expect(upload).toHaveBeenCalledWith({ "d/custom_x.xml": "<chummer/>" }, ["a>1", "b>1"]),
    );
    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith({ settings: { ...withCustom, dataset: "abc123" } }),
    );
    expect(screen.getByText(/217 件適用/)).toBeDefined();
  });

  it("names what the merge could not apply", async () => {
    vi.spyOn(api, "uploadCustomData").mockResolvedValue({
      dataset: "abc",
      applied: 3,
      skipped: [{ source: "codex/amend_critters.xml", reason: "critters.xml is not part of it" }],
    });
    setup(withCustom);
    const file = new File(["<chummer/>"], "x.xml", { type: "text/xml" });
    Object.defineProperty(file, "webkitRelativePath", { value: "cd/d/x.xml" });
    fireEvent.change(screen.getByLabelText("カスタムデータを読み込む（2 件必要）"), {
      target: { files: [file] },
    });
    await waitFor(() => expect(screen.getByText(/amend_critters/)).toBeDefined());
  });
});
