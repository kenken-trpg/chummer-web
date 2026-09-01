import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { CyberTab } from "@/components/character/tabs/CyberTab";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const wired = {
  id: "wired1",
  name: "Wired Reflexes",
  category: "Cyberware",
  ess: "2",
  cost: "39000",
  minrating: 1,
  maxrating: 3,
  plugin: false,
  has_wireless: true,
  source: "SR5",
  page: "",
};
const datajack = {
  id: "datajack",
  name: "Datajack",
  category: "Cyberware",
  ess: "0.1",
  cost: "1000",
  minrating: 1,
  maxrating: 1,
  plugin: true,
  has_wireless: true,
  source: "SR5",
  page: "",
};

function cyberCatalog(items: any[] = [wired, datajack]) {
  return makeCatalog({
    cyberware: {
      items,
      grades: [
        { name: "Standard", ess: 1, cost: 1 },
        { name: "Alphaware", ess: 0.8, cost: 1.2 },
      ],
    },
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
    <CyberTab
      catalog={over.catalog ?? cyberCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<CyberTab>", () => {
  it("renders the essence line, search box and Redliner toggles", () => {
    renderTab();
    expect(screen.getByText(/装着中 0 ・ Essence 6/)).toBeDefined();
    expect(screen.getByPlaceholderText("サイバーウェアを検索")).toBeDefined();
    expect(screen.getByText("胴")).toBeDefined();
    expect(screen.getByText("頭蓋")).toBeDefined();
  });

  it("lists the catalog and adds a piece at the selected grade", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Wired Reflexes"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({
      cyberware: [
        expect.objectContaining({
          ware_id: "wired1",
          rating: 1,
          grade: "Standard",
          wireless: true,
        }),
      ],
    });
  });

  it("filters the catalog by the search box", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("サイバーウェアを検索"), {
      target: { value: "datajack" },
    });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Datajack"]);
  });

  it("toggles a Redliner option through patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.click(screen.getByLabelText("胴"));
    expect(patch).toHaveBeenCalledWith({
      options: { redliner_torso: true, redliner_skull: false },
    });
  });
});
