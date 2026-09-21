import { screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { renderTab } from "./SkillsTab.helpers";

const priority = (over: Record<string, unknown> = {}) =>
  ({
    skills: { Blades: 4 },
    skill_specializations: { Blades: "Swords" },
    derived: { skill_totals: { Blades: 4 }, skill_karma: { levels: {} } },
    ...over,
  }) as never;

describe("<SkillsTab> specialization bought with karma", () => {
  it("ticks the spec onto karma", () => {
    const patch = vi.fn();
    renderTab({ patch, character: priority() });
    fireEvent.click(screen.getByLabelText("Blades カルマで"));
    expect(patch).toHaveBeenCalledWith({ skill_specs_karma: ["Blades"] });
  });

  it("unticks it again", () => {
    const patch = vi.fn();
    renderTab({ patch, character: priority({ skill_specs_karma: ["Blades"] }) });
    const box = screen.getByLabelText("Blades カルマで") as HTMLInputElement;
    expect(box.checked).toBe(true);
    fireEvent.click(box);
    expect(patch).toHaveBeenCalledWith({ skill_specs_karma: [] });
  });

  it("is not offered without a spec", () => {
    renderTab({ character: priority({ skill_specializations: {} }) });
    expect(screen.queryByLabelText("Blades カルマで")).toBeNull();
  });
});
