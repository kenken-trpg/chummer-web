import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { describe, expect, it, vi } from "vitest";
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
