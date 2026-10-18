import { render } from "@testing-library/react";
import { CritterPowerRow } from "@/components/character/CritterPowerRow";
import { critterPowerRow } from "@/lib/spell-terms";
import { testUi } from "@/tests/fixtures";

const shift = {
  name: "Shift (Metahuman Form)",
  type: "M",
  action: "Complex",
  range: "Self",
  duration: "Special",
};
const tr = (name: string) => name;

describe("<CritterPowerRow>", () => {
  it("keeps the bracketed terms in one piece, so a line breaks before them", () => {
    const { container } = render(<CritterPowerRow power={shift} tr={tr} ui={testUi} />);
    const group = container.querySelector(".term-group");
    expect(group?.textContent).toBe(
      critterPowerRow(shift, tr, testUi).slice("Shift (Metahuman Form)".length).trimStart(),
    );
    expect(group?.textContent).toMatch(/^[（(]/);
    expect(container.textContent).toBe(critterPowerRow(shift, tr, testUi));
  });

  it("prints a power the data leaves blank as its name alone", () => {
    const { container } = render(
      <CritterPowerRow power={{ name: "Mimicry" }} tr={tr} ui={testUi} />,
    );
    expect(container.querySelector(".term-group")).toBeNull();
    expect(container.textContent).toBe("Mimicry");
  });
});
