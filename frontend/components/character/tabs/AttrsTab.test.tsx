import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { AttrsTab } from "@/components/character/tabs/AttrsTab";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    patch?: (b: Record<string, unknown>) => void;
    setCharacter?: (c: any) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <AttrsTab
      catalog={makeCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={over.setCharacter ?? (() => {})}
    />,
  );
}

describe("<AttrsTab>", () => {
  it("renders the 9 physical/mental sliders and the point line, hiding MAG/RES", () => {
    renderTab();
    expect(screen.getAllByRole("slider")).toHaveLength(9);
    expect(screen.getByText(/能力値点 0\/0 ・ 特殊点 0\/0/)).toBeDefined();
  });

  it("shows the MAG row once the MAG tab is enabled", () => {
    renderTab({ character: { derived: { enabled_tabs: ["MAG"], totals: { MAG: 4 } as any } } });
    expect(screen.getAllByRole("slider")).toHaveLength(10);
  });

  it("drags STR: onChange previews via setCharacter, onMouseUp commits via patch", () => {
    const patch = vi.fn();
    // AttrsTab is a controlled slider — the preview only sticks if setCharacter
    // actually re-renders it, so drive it through real state here.
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter());
      return (
        <AttrsTab
          catalog={makeCatalog()}
          character={ch}
          d={ch.derived}
          tr={identityTr}
          trGroup={identityTr}
          t={(k) => k}
          ui={testUi}
          patch={patch}
          setCharacter={setCh}
        />
      );
    }
    render(<Harness />);
    const str = screen.getAllByRole("slider")[3]; // BOD, AGI, REA, STR
    fireEvent.change(str, { target: { value: "5" } });
    expect((str as HTMLInputElement).value).toBe("5");
    fireEvent.mouseUp(str);
    expect(patch).toHaveBeenCalledWith({ attributes: expect.objectContaining({ STR: 5 }) });
  });
});
