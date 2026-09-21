import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { MiscDrugsGear } from "@/components/character/tabs/gear/MiscDrugsGear";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const rope = {
  id: "rope",
  name: "Climbing Rope",
  category: "Tools",
  minrating: 0,
  maxrating: 0,
  cost: 30,
  avail: "-",
  source: "SR5",
};
const kit = { ...rope, id: "kit", name: "Survival Kit", category: "Survival Gear" };
const jazz = {
  id: "jazz",
  name: "Jazz",
  category: "Drugs",
  minrating: 0,
  maxrating: 0,
  cost: 75,
  avail: "-",
  source: "SR5",
};

function renderTab(
  mode: "misc" | "drugs",
  over: {
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter();
  return render(
    <MiscDrugsGear
      {...panelProps(ch, {
        catalog: over.catalog ?? makeCatalog({ gear: [rope, kit, jazz] as never }),
        patch: over.patch ?? (() => {}),
      })}
      mode={mode}
    />,
  );
}

describe("<MiscDrugsGear>", () => {
  it("lists non-drug gear in misc mode and buys via patch", () => {
    const patch = vi.fn();
    renderTab("misc", { patch });
    expect(screen.getByPlaceholderText("ギアを検索")).toBeDefined();
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Climbing Rope", "Survival Kit"]);
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Climbing Rope"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({
      gear: [{ gear_id: "rope", rating: 1, extra: undefined }],
    });
  });

  it("lists only drug-category gear in drugs mode", () => {
    renderTab("drugs");
    expect(screen.getByPlaceholderText("ドラッグ／毒物を検索")).toBeDefined();
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Jazz"]);
  });
});
