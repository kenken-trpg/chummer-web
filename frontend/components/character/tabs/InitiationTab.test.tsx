import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { InitiationTab } from "@/components/character/tabs/InitiationTab";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter({ talent: "Magician", ...over.character });
  return render(
    <InitiationTab
      catalog={over.catalog ?? makeCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<InitiationTab>", () => {
  it("renders the grade line and the grade slider", () => {
    renderTab();
    expect(screen.getByText(/等級 0 ・ カルマ 0/)).toBeDefined();
    expect(screen.getByRole("slider")).toBeDefined();
  });

  it("raising the grade patches initiate_grade + one row per grade", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter({ talent: "Magician" }));
      return (
        <InitiationTab
          catalog={makeCatalog()}
          character={ch}
          d={ch.derived}
          tr={identityTr}
          t={(k) => k}
          ui={testUi}
          patch={patch}
          setCharacter={setCh}
        />
      );
    }
    render(<Harness />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "2" } });
    fireEvent.mouseUp(slider);
    expect(patch).toHaveBeenCalledWith({
      initiate_grade: 2,
      initiations: [
        { grade: 1, kind: "metamagic", option_id: "" },
        { grade: 2, kind: "metamagic", option_id: "" },
      ],
    });
  });

  it("picking a metamagic for a grade choice patches the initiations row", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        initiate_grade: 1,
        initiations: [{ grade: 1, kind: "metamagic", option_id: "" }] as any,
        derived: { initiation: { choices: [{ grade: 1, karma: 13 }] } as any },
      },
      catalog: makeCatalog({
        metamagics: [{ id: "cf", name: "Centering", magician: true, adept: false }] as any,
      }),
      patch,
    });
    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[selects.length - 1], { target: { value: "cf" } });
    expect(patch).toHaveBeenCalledWith({
      initiations: [{ grade: 1, kind: "metamagic", option_id: "cf" }],
    });
  });
});
