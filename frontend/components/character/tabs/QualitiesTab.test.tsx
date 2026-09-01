import { render, screen } from "@testing-library/react";
import { QualitiesTab } from "@/components/character/tabs/QualitiesTab";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

function renderTab(overrides: Parameters<typeof makeCharacter>[0] = {}) {
  const ch = makeCharacter(overrides);
  return render(
    <QualitiesTab
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

describe("<QualitiesTab>", () => {
  it("renders the search box + karma line for an empty character", () => {
    renderTab();
    expect(screen.getByPlaceholderText("資質を検索")).toBeDefined();
    expect(screen.getByText(/カルマ 25 \/ 25/)).toBeDefined();
    // no owned qualities -> no 取得済み heading
    expect(screen.queryByRole("heading", { name: "取得済み" })).toBeNull();
  });

  it("shows the owned list + a text extra-editor for a needs_extra quality", () => {
    renderTab({
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
    });
    expect(screen.getByRole("heading", { name: "取得済み" })).toBeDefined();
    expect(screen.getByText("Distinctive Style")).toBeDefined();
    // renderExtraEditor("text", no options) -> a free-text input
    expect(screen.getByPlaceholderText("対象（花粉、日光など）")).toBeDefined();
  });
});
