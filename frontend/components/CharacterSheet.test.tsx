import { fireEvent, render, screen } from "@testing-library/react";
import CharacterSheet from "@/components/CharacterSheet";
import {
  identityTr,
  makeCatalog,
  makeCharacter,
  RICH_CATALOG,
  RICH_CHARACTER,
} from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const headings = () => screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);

describe("<CharacterSheet>", () => {
  it("renders an empty character: header + only the always-on コア section", () => {
    render(
      <CharacterSheet
        character={makeCharacter({ name: "Nadia" })}
        catalog={makeCatalog()}
        tr={identityTr}
        layout="standard"
      />,
    );
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe("Nadia");
    expect(headings()).toEqual(["コア"]);
    // data-less sections collapse to null
    for (const gone of ["技能", "戦闘", "資質", "武道", "コンタクト", "記述"]) {
      expect(screen.queryByText(gone)).toBeNull();
    }
  });

  it("renders the compact layout as an <article>", () => {
    const { container } = render(
      <CharacterSheet
        character={makeCharacter()}
        catalog={makeCatalog()}
        tr={identityTr}
        layout="compact"
      />,
    );
    expect(container.querySelector("article.character-sheet--compact")).not.toBeNull();
    expect(container.textContent).toContain("Shadowrun 5e");
  });

  it("renders the print layout: --print article, stat block + condition monitor, page-2 wrapper", () => {
    const { container } = render(
      <CharacterSheet
        character={makeCharacter({ name: "Volt" })}
        catalog={makeCatalog()}
        tr={identityTr}
        layout="print"
      />,
    );
    expect(container.querySelector("article.character-sheet--print")).not.toBeNull();
    expect(container.querySelector("section.print-statblock")).not.toBeNull();
    expect(container.querySelector("section.print-cm")).not.toBeNull();
    // the page-2 wrapper exists and is a direct child of the sheet (CSS break-before)
    expect(
      container.querySelector("article.character-sheet--print > .print-page-2"),
    ).not.toBeNull();
    // CoreSection is replaced by the print stat block, not rendered alongside it
    expect(container.querySelector(".sheet-core")).toBeNull();
    const h3 = headings();
    expect(h3).toEqual(expect.arrayContaining(["ステータス", "コンディションモニター"]));
    expect(h3).not.toContain("コア");
  });

  it("renders the text layout as a non-empty <pre>", () => {
    const { container } = render(
      <CharacterSheet
        character={makeCharacter({ name: "Grey" })}
        catalog={makeCatalog()}
        tr={identityTr}
        layout="text"
      />,
    );
    const pre = container.querySelector("pre.sheet-text");
    expect(pre).not.toBeNull();
    expect(pre?.textContent).toContain("Grey");
    expect(pre?.textContent).toContain("=== 能力値 ===");
  });

  it("shows a section once its data is present", () => {
    const seen: string[] = [];
    const tr = (n: string) => {
      seen.push(n);
      return n;
    };
    render(
      <CharacterSheet
        character={makeCharacter({
          derived: {
            qualities: [
              { id: "q1", name: "Ambidextrous", karma: -4, category: "Positive", source: "SR5" },
            ] as any,
            martial_arts: [
              {
                id: "m1",
                art_id: "a1",
                name: "Krav Maga",
                karma: 7,
                style_karma: 7,
                techniques: [],
                technique_options: [],
              },
            ] as any,
            contacts: [
              {
                id: "c1",
                name: "Fixer",
                role: "情報屋",
                connection: 3,
                loyalty: 2,
                cost: 0,
                connection_max: 6,
                loyalty_max: 6,
              },
            ] as any,
          },
        })}
        catalog={makeCatalog()}
        tr={tr}
        layout="standard"
      />,
    );
    expect(headings()).toEqual(expect.arrayContaining(["コア", "資質", "武道", "コンタクト"]));
    // qualities + martial arts run names through `tr`; contacts render `c.name` raw
    expect(seen).toEqual(expect.arrayContaining(["Ambidextrous", "Krav Maga"]));
    expect(screen.getByText("Fixer")).toBeDefined();
  });
});

describe("<CharacterSheet> ware by name only", () => {
  beforeEach(() => localStorage.clear());
  const LABEL = "ウェアは名称のみ";
  const sheet = (layout: "standard" | "compact" | "text" | "print") =>
    render(
      <CharacterSheet
        character={RICH_CHARACTER}
        catalog={RICH_CATALOG}
        tr={identityTr}
        layout={layout}
      />,
    );

  it("folds the print sheet's ware list and remembers it", () => {
    const first = sheet("print");
    const wareList = () =>
      [...document.querySelectorAll("section.sheet-section")].find((el) =>
        el.textContent?.includes("Wired Reflexes"),
      )!;
    expect(wareList().querySelector("li")!.textContent).toContain("ESS");

    fireEvent.click(screen.getByLabelText(LABEL));
    expect(wareList().querySelector("li")!.textContent).toBe("Wired Reflexes R2");
    expect(localStorage.getItem("sheetWareNames")).toBe("1");
    // the switch is chrome, not sheet: it stays off paper
    expect(screen.getByLabelText(LABEL).closest(".no-print")).not.toBeNull();

    first.unmount();
    sheet("text");
    expect(document.querySelector("pre.sheet-text")!.textContent).not.toContain("ESS −2");
  });

  it("has no switch on the compact sheet, which is names-only already", () => {
    sheet("compact");
    expect(screen.queryByLabelText(LABEL)).toBeNull();
  });
});
