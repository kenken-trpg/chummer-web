import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { QualitiesTab } from "@/components/character/tabs/QualitiesTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const pickerCatalog = makeCatalog({
  qualities: [
    { id: "amb", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" },
    { id: "dist", name: "Distinctive Style", karma: -5, category: "Negative", source: "SR5" },
  ] as any,
});

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <QualitiesTab
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

describe("<QualitiesTab>", () => {
  it("renders the search box + karma line for an empty character", () => {
    renderTab();
    expect(screen.getByPlaceholderText("資質を検索")).toBeDefined();
    expect(screen.getByText(/カルマ 25 \/ 25/)).toBeDefined();
    expect(screen.queryByRole("heading", { name: "取得済み" })).toBeNull();
  });

  it("shows the owned list + a text extra-editor for a needs_extra quality", () => {
    renderTab({
      character: {
        derived: {
          qualities: [
            {
              id: "q1",
              name: "Distinctive Style",
              karma: -5,
              category: "Negative",
              source: "SR5",
              needs_extra: true,
              extra_kind: "text",
            },
          ] as any,
        },
      },
    });
    expect(screen.getByRole("heading", { name: "取得済み" })).toBeDefined();
    expect(screen.getByText("Distinctive Style")).toBeDefined();
    expect(screen.getByPlaceholderText("対象（花粉、日光など）")).toBeDefined();
  });

  it("lists SR5 catalog qualities and filters by the category tabs", () => {
    renderTab({ catalog: pickerCatalog });
    const list = document.querySelector(".quality-list") as HTMLElement;
    const names = () => [...list.querySelectorAll("b")].map((b) => b.textContent);
    expect(names()).toEqual(["Ambidextrous", "Distinctive Style"]);

    fireEvent.click(screen.getByRole("button", { name: "不利" }));
    expect(names()).toEqual(["Distinctive Style"]);
  });

  it("filters by the search box", () => {
    renderTab({ catalog: pickerCatalog });
    fireEvent.change(screen.getByPlaceholderText("資質を検索"), { target: { value: "ambi" } });
    const list = document.querySelector(".quality-list") as HTMLElement;
    expect([...list.querySelectorAll("b")].map((b) => b.textContent)).toEqual(["Ambidextrous"]);
  });

  it("'追加' patches quality_ids with the picked id", () => {
    const patch = vi.fn();
    renderTab({ catalog: pickerCatalog, patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Ambidextrous"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(expect.objectContaining({ quality_ids: ["amb"] }));
  });
});

describe("<QualitiesTab> a limit shared between siblings", () => {
  // Indomitable (SR5 p.75): three kinds, 3 takes across all of them
  const kinds = ["Physical", "Mental", "Social"].map((k) => `Indomitable (${k})`);
  const catalog = makeCatalog({
    qualities: kinds.map((name, i) => ({
      id: `ind${i}`,
      name,
      karma: 8,
      category: "Positive",
      source: "SR5",
      max_takes: 3,
      include_in_limit: kinds.filter((other) => other !== name),
    })) as any,
  });
  const row = (name: string) =>
    [...document.querySelectorAll(".quality-list .quality-item")].find(
      (el) => el.querySelector("b")?.textContent === name,
    )!;

  it("says the limit is shared", () => {
    renderTab({ catalog });
    expect(row("Indomitable (Social)").textContent).toContain(
      "Indomitable (Physical)、Indomitable (Mental) と合わせて最大3",
    );
  });

  it("stops the add once the siblings hold the whole limit", () => {
    const patch = vi.fn();
    renderTab({ catalog, patch, character: { quality_ids: ["ind0", "ind0", "ind1"] } });
    const social = row("Indomitable (Social)").querySelector("button")!;
    expect(social.disabled).toBe(true);
    fireEvent.click(social);
    expect(patch).not.toHaveBeenCalled();
  });

  it("still adds while the shared count is under it", () => {
    const patch = vi.fn();
    renderTab({ catalog, patch, character: { quality_ids: ["ind0"] } });
    fireEvent.click(row("Indomitable (Social)").querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(expect.objectContaining({ quality_ids: ["ind0", "ind2"] }));
  });
});

describe("<QualitiesTab> a cost moved by a condition", () => {
  it("shows the table karma beside the one charged", () => {
    renderTab({
      character: {
        quality_ids: ["blind"],
        derived: {
          qualities: [
            {
              id: "blind",
              name: "Blind",
              karma: -5,
              karma_base: -15,
              category: "Negative",
              source: "RF",
            },
          ] as any,
        },
      },
    });
    const owned = [...document.querySelectorAll(".quality-item")].find((el) =>
      el.textContent?.includes("Blind"),
    )!;
    expect(owned.textContent).toContain("カルマ -5（条件で変動・表では -15）");
  });
});

describe("<QualitiesTab> career prices (SR5 p.107)", () => {
  const catalog = makeCatalog({
    qualities: [
      { id: "amb", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" },
      { id: "dist", name: "Distinctive Style", karma: -5, category: "Negative", source: "SR5" },
      {
        id: "way",
        name: "The Artist's Way",
        karma: 20,
        category: "Positive",
        source: "SR5",
        double_career: false,
      },
    ] as any,
  });
  const itemText = (scope: string, name: string) =>
    [...document.querySelectorAll(`${scope} .quality-item`)].find(
      (el) => el.querySelector("b")?.textContent === name,
    )!.textContent;

  it("prices the catalog at the career rate", () => {
    renderTab({ catalog, character: { derived: { quality_career_pricing: true } as any } });
    expect(itemText(".quality-list", "Ambidextrous")).toContain("キャリアでは 8カルマ");
    expect(itemText(".quality-list", "The Artist's Way")).toContain("キャリアでは 20カルマ");
    expect(itemText(".quality-list", "Distinctive Style")).toContain("キャリアではカルマなし");
  });

  it("says what a taken one cost and what a held negative would take to buy off", () => {
    renderTab({
      catalog,
      character: {
        quality_ids: ["amb", "dist"],
        derived: {
          quality_career_pricing: true,
          qualities: [
            {
              id: "amb",
              name: "Ambidextrous",
              karma: 4,
              category: "Positive",
              source: "SR5",
              career_cost: 8,
            },
            {
              id: "dist",
              name: "Distinctive Style",
              karma: -5,
              category: "Negative",
              source: "SR5",
            },
          ],
        } as any,
      },
    });
    expect(itemText(".card", "Ambidextrous")).toContain("キャリアで取得（8カルマ）");
    expect(itemText(".card", "Distinctive Style")).toContain("外すと買い戻し 10カルマ");
  });

  it("lists the qualities dropped in career", () => {
    renderTab({
      catalog,
      character: {
        derived: {
          quality_career_pricing: true,
          qualities_removed: [
            { id: "dist", name: "Distinctive Style", category: "Negative", karma: 10 },
          ],
        } as any,
      },
    });
    expect(screen.getByText("キャリアで外した資質")).toBeTruthy();
    expect(document.body.textContent).toContain("買い戻し 10カルマ");
  });

  it("stays quiet outside career", () => {
    renderTab({ catalog });
    expect(document.body.textContent).not.toContain("キャリアでは");
  });
});

describe("<QualitiesTab> karma overspent", () => {
  const line = () => document.querySelector(".card > p.muted")!;

  it("turns the karma line red and says so", () => {
    renderTab({ character: { derived: { karma: { pool: 25, spent: 29, remaining: -4 } } as any } });
    expect(line().className).toContain("errors");
    expect(line().textContent).toContain("カルマが不足しています（残り -4）");
  });

  it("leaves it plain while there is karma left", () => {
    renderTab();
    expect(line().className).not.toContain("errors");
    expect(line().textContent).not.toContain("不足");
  });
});
