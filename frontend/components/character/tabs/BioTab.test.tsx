import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { BioTab } from "@/components/character/tabs/BioTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

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

function bioCatalog(items: object[] = [muscle, toner]) {
  return makeCatalog({
    bioware: { items, grades: [{ name: "Standard", ess: 1, cost: 1 }] },
  } as never);
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
      {...panelProps(ch, {
        catalog: over.catalog ?? bioCatalog(),
        patch: over.patch ?? (() => {}),
      })}
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

describe("<BioTab> compact view", () => {
  beforeEach(() => localStorage.clear());

  it("shares the cyberware tab's name-only switch", () => {
    // one setting for both tabs: set it here as if the cyber tab had
    localStorage.setItem("wareCompact", "1");
    renderTab({
      character: {
        bioware: [{ id: "b1", ware_id: "musc", rating: 3, grade: "Standard" }],
        derived: {
          bioware: [
            {
              id: "b1",
              ware_id: "musc",
              name: "Muscle Augmentation",
              category: "Bioware",
              grade: "Standard",
              rating: 3,
              essence: 0.6,
              nuyen: 93000,
              source: "SR5",
            },
          ],
        },
      } as never,
    });
    expect((screen.getByLabelText("簡易表示（名称のみ）") as HTMLInputElement).checked).toBe(true);
    expect(screen.getByText("Muscle Augmentation R3")).toBeDefined();
    expect(document.querySelectorAll(".cyber-item .cyber-controls")).toHaveLength(0);

    fireEvent.click(screen.getByLabelText("簡易表示（名称のみ）"));
    expect(document.querySelectorAll(".cyber-item .cyber-controls").length).toBeGreaterThan(0);
    expect(localStorage.getItem("wareCompact")).toBe("0");
  });
});

describe("<BioTab> a player-priced piece", () => {
  it("offers a price field held to the range and patches the pick", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        bioware: [{ id: "b1", ware_id: "sculpt", rating: 1, grade: "Standard", cost: 1000 }],
        derived: {
          bioware: [
            {
              id: "b1",
              ware_id: "sculpt",
              name: "Moderate Biosculpting Modification",
              category: "Biosculpting",
              grade: "Standard",
              rating: 1,
              essence: 0,
              nuyen: 1000,
              cost: 1000,
              cost_range: [500, 2000],
              source: "CF",
            },
          ],
        },
      } as never,
    });
    const field = screen.getByLabelText(/Moderate Biosculpting Modification: /) as HTMLInputElement;
    expect(field.value).toBe("1000");
    fireEvent.change(field, { target: { value: "5000" } });
    expect(patch).toHaveBeenLastCalledWith({
      bioware: [{ id: "b1", ware_id: "sculpt", rating: 1, grade: "Standard", cost: 2000 }],
    });
  });

  it("shows no price field for a fixed-price piece", () => {
    renderTab({
      character: {
        bioware: [{ id: "b1", ware_id: "musc", rating: 1, grade: "Standard" }],
        derived: {
          bioware: [
            {
              id: "b1",
              ware_id: "musc",
              name: "Muscle Augmentation",
              category: "Bioware",
              grade: "Standard",
              rating: 1,
              essence: 0.2,
              nuyen: 31000,
              source: "SR5",
            },
          ],
        },
      } as never,
    });
    expect(screen.queryByLabelText(/Muscle Augmentation: /)).toBeNull();
  });
});
