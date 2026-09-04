import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SpritesTab } from "@/components/character/tabs/SpritesTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const courier = { id: "cs", name: "Courier Sprite", source: "SR5" };

function renderTab(patch: (b: Record<string, unknown>) => void = () => {}) {
  const ch = makeCharacter();
  return render(
    <SpritesTab
      catalog={makeCatalog({ sprites: [courier] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={() => {}}
    />,
  );
}

describe("<SpritesTab>", () => {
  it("renders the intro line and the search box", () => {
    renderTab();
    expect(screen.getByPlaceholderText("スプライトを検索")).toBeDefined();
    expect(screen.getByText("Courier Sprite")).toBeDefined();
  });

  it("compiles and registers a sprite via patch", () => {
    const patch = vi.fn();
    renderTab(patch);
    fireEvent.click(screen.getByRole("button", { name: "コンパイル" }));
    expect(patch).toHaveBeenCalledWith({
      sprites: [{ sprite_id: "cs", level: 1, registered: false }],
    });
    fireEvent.click(screen.getByRole("button", { name: "登録" }));
    expect(patch).toHaveBeenCalledWith({
      sprites: [{ sprite_id: "cs", level: 1, registered: true }],
    });
  });
});
