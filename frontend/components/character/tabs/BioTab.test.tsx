import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { BioTab } from "@/components/character/tabs/BioTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const muscle = {
  id: "musc",
  name: "Muscle Augmentation",
  category: "Bioware",
  ess: "0.2",
  cost: "31000",
  minrating: 1,
  maxrating: 4,
  plugin: false,
  has_wireless: false,
  source: "SR5",
  page: "",
};
const toner = {
  id: "toner",
  name: "Muscle Toner",
  category: "Bioware",
  ess: "0.2",
  cost: "32000",
  minrating: 1,
  maxrating: 4,
  plugin: false,
  has_wireless: false,
  source: "SR5",
  page: "",
};

function bioCatalog(items: any[] = [muscle, toner]) {
  return makeCatalog({
    bioware: { items, grades: [{ name: "Standard", ess: 1, cost: 1 }] },
  } as any);
}

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <BioTab
      catalog={over.catalog ?? bioCatalog()}
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

describe("<BioTab>", () => {
  it("renders the essence line and the search box", () => {
    renderTab();
    expect(screen.getByText(/装着中 0 ・ Essence 6（バイオ −0）/)).toBeDefined();
    expect(screen.getByPlaceholderText("バイオウェアを検索")).toBeDefined();
  });

  it("adds a catalog piece via patch at min rating", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Muscle Augmentation"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({
      bioware: [
        expect.objectContaining({ ware_id: "musc", rating: 1, grade: "Standard", wireless: true }),
      ],
    });
  });

  it("filters the catalog by search", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("バイオウェアを検索"), {
      target: { value: "toner" },
    });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Muscle Toner"]);
  });
});
