import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { GearTab } from "@/components/character/tabs/GearTab";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

function renderTab() {
  const ch = makeCharacter();
  return render(
    <GearTab
      catalog={makeCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      patch={() => {}}
      setCharacter={() => {}}
    />,
  );
}

describe("<GearTab>", () => {
  it("renders the money line and the kind tab row, defaulting to Armor", () => {
    renderTab();
    expect(screen.getByText(/作成時の購入/)).toBeDefined();
    for (const label of [
      "防具",
      "武器",
      "車両",
      "ドローン",
      "ギア",
      "ドラッグ",
      "ライフスタイル",
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeDefined();
    }
    expect(screen.getByPlaceholderText("防具を検索")).toBeDefined();
  });

  it("swaps the sub-panel when another kind tab is clicked", () => {
    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "武器" }));
    expect(screen.getByRole("button", { name: "武器" }).className).toContain("active");
    expect(screen.getByPlaceholderText("武器を検索")).toBeDefined();
    expect(screen.queryByPlaceholderText("防具を検索")).toBeNull();
  });
});
