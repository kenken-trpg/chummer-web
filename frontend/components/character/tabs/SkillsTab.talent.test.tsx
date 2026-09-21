import { screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { renderTab } from "./SkillsTab.helpers";

const talent = {
  qty: 2,
  rating: 5,
  group: false,
  options: ["Alchemy", "Counterspelling", "Spellcasting"],
  picked: ["Spellcasting"],
};

describe("<SkillsTab> talent skills", () => {
  it("offers one select per free skill, each without the other's pick", () => {
    renderTab({ character: { derived: { talent_skills: talent } } as never });
    expect(screen.getByText("タレントでもらえる技能（2 つを R5 で）")).toBeDefined();
    const first = screen.getByLabelText("1 つ目") as HTMLSelectElement;
    const second = screen.getByLabelText("2 つ目") as HTMLSelectElement;
    expect(first.value).toBe("Spellcasting");
    expect([...second.options].map((o) => o.value)).toEqual(["", "Alchemy", "Counterspelling"]);
  });

  it("takes the free levels back off a replaced pick and keeps what points bought", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        skills: { Spellcasting: 6, Alchemy: 2 },
        talent_skills: ["Spellcasting"],
        derived: { talent_skills: talent },
      } as never,
    });
    fireEvent.change(screen.getByLabelText("1 つ目"), { target: { value: "Counterspelling" } });
    expect(patch).toHaveBeenLastCalledWith({
      talent_skills: ["Counterspelling"],
      skills: { Spellcasting: 1, Alchemy: 2 },
    });
  });

  it("shows nothing when the talent gives no free skills", () => {
    renderTab({
      character: { derived: { talent_skills: { ...talent, qty: 0, picked: [] } } } as never,
    });
    expect(screen.queryByLabelText("1 つ目")).toBeNull();
  });
});
