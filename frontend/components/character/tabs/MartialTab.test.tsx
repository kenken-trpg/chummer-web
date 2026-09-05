import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { MartialTab } from "@/components/character/tabs/MartialTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const catStyle = {
  id: "s1",
  name: "Karate",
  cost: 7,
  source: "SR5",
  techniques: ["Kick Attack", "Set-Up"],
};

const ownedStyle = {
  id: "m1",
  art_id: "s1",
  name: "Karate",
  style_karma: 7,
  karma: 7,
  source: "SR5",
  techniques: [{ name: "Kick Attack", free: true, karma: 0 }],
  technique_options: ["Kick Attack", "Set-Up"],
  technique_max: null,
};

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <MartialTab
      catalog={over.catalog ?? makeCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<MartialTab>", () => {
  it("shows the point line and the search box for an empty character", () => {
    renderTab();
    expect(screen.getByText(/流派 0\/1 ・ 技 0\/5/)).toBeDefined();
    expect(screen.getByPlaceholderText("武道を検索")).toBeDefined();
  });

  it("filters the catalog and acquires a style with its first technique", () => {
    const patch = vi.fn();
    renderTab({ catalog: makeCatalog({ martial_arts: [catStyle] as any }), patch });
    fireEvent.change(screen.getByPlaceholderText("武道を検索"), { target: { value: "kara" } });
    fireEvent.click(screen.getByRole("button", { name: "取得" }));
    expect(patch).toHaveBeenCalledWith({
      martial_arts: [{ art_id: "s1", techniques: ["Kick Attack"] }],
    });
  });

  it("disables acquire once the style cap is reached", () => {
    renderTab({
      catalog: makeCatalog({ martial_arts: [catStyle] as any }),
      character: { derived: { martial_art_points: { styles: 1, style_max: 1 } as any } },
    });
    expect(screen.getByRole("button", { name: "上限" })).toHaveProperty("disabled", true);
  });

  it("toggles a technique on an owned style through patch", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        martial_arts: [{ id: "m1", art_id: "s1", techniques: ["Kick Attack"] } as any],
        derived: { martial_arts: [ownedStyle] as any },
      },
      patch,
    });
    const boxes = screen.getAllByRole("checkbox");
    fireEvent.click(boxes[1]); // Set-Up
    expect(patch).toHaveBeenCalledWith({
      martial_arts: [{ id: "m1", art_id: "s1", techniques: ["Kick Attack", "Set-Up"] }],
    });
  });
});
