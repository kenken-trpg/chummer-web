import { screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import { makeCharacter, panelProps } from "@/tests/fixtures";
import { blades, exoticSkill, skillsCatalog, renderTab, renderStateful } from "./SkillsTab.helpers";

describe("<SkillsTab> specialisations", () => {
  it("commits the chosen spec, and clearing it drops the key rather than storing ''", () => {
    const patch = vi.fn();
    const setCharacter = vi.fn();
    renderTab({
      patch,
      setCharacter,
      character: {
        skills: { Blades: 4 },
        skill_specializations: { Blades: "Swords" },
        derived: { skill_totals: { Blades: 4 } },
      } as never,
    });

    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "" } });

    expect(patch).toHaveBeenCalledWith({ skill_specializations: {} });
    // the local copy has to move too, or the select snaps back before the
    // round trip finishes
    expect(setCharacter.mock.calls[0][0].skill_specializations).toEqual({});
  });

  it("is disabled until the character actually has the skill", () => {
    const { rerender } = renderTab();
    expect((screen.getAllByRole("combobox")[0] as HTMLSelectElement).disabled).toBe(true);

    const ch = makeCharacter({ skills: { Blades: 1 }, derived: { skill_totals: { Blades: 1 } } });
    rerender(<SkillsTab {...panelProps(ch, { catalog: skillsCatalog() })} />);
    expect((screen.getAllByRole("combobox")[0] as HTMLSelectElement).disabled).toBe(false);
  });

  it("an expertise from a quality fills the spec and locks it", () => {
    // the character did not buy this one and cannot change it
    renderTab({
      character: {
        skills: { Blades: 4 },
        derived: {
          skill_totals: { Blades: 4 },
          skill_expertises: [{ skill: "Blades", spec: "Swords", bonus: 3, source: "Aptitude" }],
        },
      } as never,
    });

    const select = screen.getAllByRole("combobox")[0] as HTMLSelectElement;
    expect(select.value).toBe("Swords");
    expect(select.disabled).toBe(true);
  });
});

describe("<SkillsTab> exotic skills", () => {
  const exoticRow = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    skill_name: name,
    label: name,
    attribute: "AGI",
    rating: 1,
    rating_max: 6,
    options: ["Blowgun", "Net"],
    extra: "",
    ...over,
  });

  function withExotics(
    rows: Record<string, unknown>[],
    patch: (b: Record<string, unknown>) => void,
  ) {
    return renderStateful(
      patch,
      { exotic_skills: rows, derived: { exotic_skills: rows } } as never,
      skillsCatalog({ skills: [blades, exoticSkill] }),
    );
  }

  /** The `<SpecPicker>` of one exotic row — several selects are on screen. */
  const targetPicker = (index: number) =>
    screen
      .getAllByRole("combobox")
      .filter((el) => [...el.querySelectorAll("option")].some((o) => o.textContent === "Blowgun"))[
      index
    ];

  it("says so when there are none", () => {
    renderTab();
    expect(screen.getByText("まだありません。下のボタンから追加します。")).toBeDefined();
  });

  it("commits a rating on the row that moved, not on both", () => {
    const patch = vi.fn();
    withExotics(
      [exoticRow("e1", "Exotic Ranged Weapon"), exoticRow("e2", "Exotic Melee Weapon")],
      patch,
    );

    const slider = screen.getAllByRole("slider").at(-1)!;
    fireEvent.change(slider, { target: { value: "5" } });
    fireEvent.mouseUp(slider);

    const rows = patch.mock.calls[0][0].exotic_skills as { id: string; rating: number }[];
    expect(rows.find((r) => r.id === "e1")?.rating).toBe(1);
    expect(rows.find((r) => r.id === "e2")?.rating).toBe(5);
  });

  it("commits the weapon a row is for, on that row only", () => {
    const patch = vi.fn();
    withExotics(
      [exoticRow("e1", "Exotic Ranged Weapon"), exoticRow("e2", "Exotic Melee Weapon")],
      patch,
    );

    fireEvent.change(targetPicker(1), { target: { value: "Net" } });

    const rows = patch.mock.calls[0][0].exotic_skills as { id: string; extra: string }[];
    expect(rows.find((r) => r.id === "e1")?.extra).toBe("");
    expect(rows.find((r) => r.id === "e2")?.extra).toBe("Net");
  });

  it("deleting one row keeps the other", () => {
    const patch = vi.fn();
    withExotics(
      [exoticRow("e1", "Exotic Ranged Weapon"), exoticRow("e2", "Exotic Melee Weapon")],
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    expect((patch.mock.calls[0][0].exotic_skills as { id: string }[]).map((r) => r.id)).toEqual([
      "e2",
    ]);
  });
});
