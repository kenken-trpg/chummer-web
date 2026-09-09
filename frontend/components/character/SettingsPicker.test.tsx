import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, type MergeResult } from "@/lib/api";
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

/** A merge response with only the fields a test cares about spelled out. */
function mergeResult(over: Partial<MergeResult>): MergeResult {
  return { dataset: "d", applied: 0, skipped: [], changes: [], truncated: false, ...over };
}

/** A `File` that reports a directory path, the way a folder pick does. */
function folderFile(path: string, text: string): File {
  const file = new File([text], path.split("/").pop() as string, { type: "text/xml" });
  Object.defineProperty(file, "webkitRelativePath", { value: path });
  return file;
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

  it("offers the folder load whether or not the ruleset needs custom data", () => {
    // the folder is how a ruleset arrives at all, so it cannot be gated on
    // having already loaded one
    setup({ name: "Standard", books: ["SR5"] });
    expect(screen.getByText("スタイル一式を読み込む")).toBeDefined();
  });

  it("uploads the folder and stores the hash on the character", async () => {
    const upload = vi
      .spyOn(api, "uploadCustomData")
      .mockResolvedValue(mergeResult({ dataset: "abc123", applied: 217 }));
    const { patch } = setup(withCustom);
    const input = screen.getByLabelText("スタイル一式を読み込む");
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
    vi.spyOn(api, "uploadCustomData").mockResolvedValue(
      mergeResult({
        dataset: "abc",
        applied: 3,
        skipped: [{ source: "codex/amend_critters.xml", reason: "critters.xml is not part of it" }],
      }),
    );
    setup(withCustom);
    const file = new File(["<chummer/>"], "x.xml", { type: "text/xml" });
    Object.defineProperty(file, "webkitRelativePath", { value: "cd/d/x.xml" });
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: { files: [file] },
    });
    await waitFor(() => expect(screen.getByText(/amend_critters/)).toBeDefined());
  });

  it("puts every settings file in a folder into the pulldown", async () => {
    // a published folder holds one ruleset per variant; picking for the user
    // would be a guess, so all of them are offered and none is applied
    const parse = vi.spyOn(api, "parseSettings").mockImplementation(async (bytes: ArrayBuffer) => ({
      settings: { name: new TextDecoder().decode(bytes), books: ["SR5"] },
      build_method: "SumToTen",
    }));
    const { patch } = setup();
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: {
        files: [
          folderFile("スタイル/settings/a.xml", "A"),
          folderFile("スタイル/settings/b.xml", "B"),
        ],
      },
    });

    await waitFor(() => expect(parse).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByRole("option", { name: "A" })).toBeDefined());
    expect(screen.getByRole("option", { name: "B" })).toBeDefined();
    expect(patch).not.toHaveBeenCalled();
  });

  it("applies the ruleset straight away when the folder holds only one", async () => {
    vi.spyOn(api, "parseSettings").mockResolvedValue({
      settings: { name: "新東京", books: ["SR5"] },
      build_method: "SumToTen",
    });
    const { patch } = setup();
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: { files: [folderFile("スタイル/settings/only.xml", "X")] },
    });
    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith(
        expect.objectContaining({ settings: { name: "新東京", books: ["SR5"] } }),
      ),
    );
  });

  it("merges the custom data on the pulldown pick, without asking for the folder again", async () => {
    // the ordering trap this replaces: the folder used to have to be picked
    // after the ruleset, and again for every ruleset in the same folder
    const upload = vi
      .spyOn(api, "uploadCustomData")
      .mockResolvedValue(mergeResult({ dataset: "hash2", applied: 5 }));
    vi.spyOn(api, "parseSettings").mockImplementation(async (bytes: ArrayBuffer) => ({
      settings: { name: new TextDecoder().decode(bytes), books: ["SR5"], customdata: ["a>1"] },
      build_method: "SumToTen",
    }));
    const { patch } = setup();
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: {
        files: [
          folderFile("スタイル/settings/a.xml", "A"),
          folderFile("スタイル/settings/b.xml", "B"),
          folderFile("スタイル/customdata/d/custom_x.xml", "<chummer/>"),
        ],
      },
    });
    await waitFor(() => expect(screen.getByRole("option", { name: "B" })).toBeDefined());

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "B" } });
    await waitFor(() =>
      expect(upload).toHaveBeenCalledWith({ "d/custom_x.xml": "<chummer/>" }, ["a>1"]),
    );
    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith(
        expect.objectContaining({
          settings: { name: "B", books: ["SR5"], customdata: ["a>1"], dataset: "hash2" },
        }),
      ),
    );
  });

  it("groups what the merge changed, so a pack can be checked against its claim", async () => {
    // the difference this exists for: `source, page` edits are a relabelling
    // of entries the app already had, additions are new game content
    vi.spyOn(api, "uploadCustomData").mockResolvedValue(
      mergeResult({
        applied: 3,
        changes: [
          { file: "qualities.xml", entry: "Adept", action: "edited", fields: ["source", "page"] },
          {
            file: "qualities.xml",
            entry: "Aptitude",
            action: "edited",
            fields: ["source", "page"],
          },
          { file: "martialarts.xml", entry: "居合道", action: "added", fields: [] },
        ],
      }),
    );
    setup(withCustom);
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: { files: [folderFile("customdata/d/custom_x.xml", "<chummer/>")] },
    });

    fireEvent.click(await screen.findByText("内訳を見る"));
    expect(screen.getByText("source, page を変更")).toBeDefined();
    expect(screen.getByText("Adept、Aptitude")).toBeDefined();
    expect(screen.getByText("追加")).toBeDefined();
    expect(screen.getByText("居合道")).toBeDefined();
  });

  it("offers no breakdown when the merge changed nothing", async () => {
    vi.spyOn(api, "uploadCustomData").mockResolvedValue(mergeResult({ applied: 0 }));
    setup(withCustom);
    fireEvent.change(screen.getByLabelText("スタイル一式を読み込む"), {
      target: { files: [folderFile("customdata/d/custom_x.xml", "<chummer/>")] },
    });
    await waitFor(() => expect(screen.getByText(/0 件適用/)).toBeDefined());
    expect(screen.queryByText("内訳を見る")).toBeNull();
  });
});
