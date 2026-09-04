import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { ComplexFormsTab } from "@/components/character/tabs/ComplexFormsTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

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
      catalog={makeCatalog({ complex_forms: [puppeteer, cleaner] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={() => {}}
    />,
  );
}

describe("<ComplexFormsTab>", () => {
  it("renders the free-slot line and the search box", () => {
    renderTab();
    expect(screen.getByText(/優先度の無料枠 0\/0/)).toBeDefined();
    expect(screen.getByPlaceholderText("複合体を検索")).toBeDefined();
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
});
