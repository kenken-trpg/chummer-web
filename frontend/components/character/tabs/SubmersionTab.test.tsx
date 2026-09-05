import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SubmersionTab } from "@/components/character/tabs/SubmersionTab";
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
  const ch = makeCharacter({ talent: "Technomancer", ...over.character });
  return render(
    <SubmersionTab
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

describe("<SubmersionTab>", () => {
  it("renders the grade line and the grade slider", () => {
    renderTab();
    expect(screen.getByText(/等級 0 ・ カルマ 0/)).toBeDefined();
    expect(screen.getByRole("slider")).toBeDefined();
  });

  it("raising the grade patches submersion_grade + one row per grade", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter({ talent: "Technomancer" }));
      return (
        <SubmersionTab
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
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "2" } });
    fireEvent.mouseUp(slider);
    expect(patch).toHaveBeenCalledWith({
      submersion_grade: 2,
      submersions: [
        { grade: 1, echo_id: "" },
        { grade: 2, echo_id: "" },
      ],
    });
  });

  it("picking an echo for a grade choice patches the submersions row", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        submersion_grade: 1,
        submersions: [{ grade: 1, echo_id: "" }] as any,
        derived: { submersion: { choices: [{ grade: 1, karma: 13 }] } as any },
      },
      catalog: makeCatalog({
        echoes: [{ id: "ov", name: "Overclocking", max_takes: 1 }] as any,
      }),
      patch,
    });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "ov" } });
    expect(patch).toHaveBeenCalledWith({
      submersions: [{ grade: 1, echo_id: "ov", extra: null }],
    });
  });
});
