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
