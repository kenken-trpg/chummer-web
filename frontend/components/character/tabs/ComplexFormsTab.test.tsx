import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { ComplexFormsTab } from "@/components/character/tabs/ComplexFormsTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const puppeteer = {
  id: "pw",
  name: "Puppeteer",
  target: "Persona",
  duration: "P",
  fv: "L-1",
  source: "SR5",
};
const cleaner = { ...puppeteer, id: "cl", name: "Cleaner" };

function renderTab(patch: (b: Record<string, unknown>) => void = () => {}) {
  const ch = makeCharacter();
  return render(
    <ComplexFormsTab
      {...panelProps(ch, {
        catalog: makeCatalog({ complex_forms: [puppeteer, cleaner] as never }),
        patch,
      })}
    />,
  );
}

describe("<ComplexFormsTab>", () => {
  it("renders the free-slot line and the search box", () => {
    renderTab();
    expect(screen.getByText(/優先度の無料枠 0\/0/)).toBeDefined();
    expect(screen.getByPlaceholderText("複合体を検索")).toBeDefined();
  });

  it("explains where the free slots come from and what the rest cost", () => {
    renderTab();
    expect(screen.getByRole("button", { name: "複合体の無料枠 の説明" })).toBeDefined();
    expect(screen.getByText(/共振の欄で選んだタレント/)).toBeDefined();
    expect(screen.getByText(/1 つずつカルマで買う/)).toBeDefined();
  });

  it("prices a form past the free ones as the settings file does", () => {
    const ch = makeCharacter({
      derived: { complex_form_points: { used: 4, free: 3, paid: 1, karma: 6, form_karma: 6 } },
    });
    render(
      <ComplexFormsTab
        {...panelProps(ch, { catalog: makeCatalog({ complex_forms: [puppeteer] as never }) })}
      />,
    );
    expect(screen.getByText(/追加 1×6カルマ/)).toBeDefined();
    // and the picker's price for the next one
    expect(screen.getByText(/\/ 6カルマ/, { selector: ".quality-item .muted" })).toBeDefined();
  });

  it("adds a complex form via patch", () => {
    const patch = vi.fn();
    renderTab(patch);
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Puppeteer"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ complex_forms: [{ form_id: "pw" }] });
  });

  it("filters the catalog by search", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("複合体を検索"), { target: { value: "clean" } });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Cleaner"]);
  });

  it("keeps a form that picks an attribute on offer after it is learned, and only that one", () => {
    const infusion = {
      ...puppeteer,
      id: "inf",
      name: "Infusion of [Matrix Attribute]",
      needs_extra: true,
    };
    const ch = makeCharacter({
      complex_forms: [
        { id: "c1", form_id: "inf", extra: "Sleaze" },
        { id: "c2", form_id: "pw" },
      ],
    });
    render(
      <ComplexFormsTab
        {...panelProps(ch, {
          catalog: makeCatalog({ complex_forms: [puppeteer, infusion] as never }),
        })}
      />,
    );
    const offered = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(offered).toEqual(["Infusion of [Matrix Attribute]"]);
  });
});
