import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import type { Character } from "@/lib/types";
import { makeCharacter, panelProps } from "@/tests/fixtures";
import {
  blades,
  exoticSkill,
  knowItem,
  skillsCatalog,
  renderTab,
  renderStateful,
  knowRow,
} from "./SkillsTab.helpers";

describe("<SkillsTab>", () => {
  it("renders the point line and the four sections", () => {
    renderTab();
    expect(screen.getByText(/技能 0\/0 ・ グループ 0\/0 ・ 知識 0\/0/)).toBeDefined();
    for (const h of ["技能グループ", "アクティブ技能", "Exotic技能", "知識技能"]) {
      expect(screen.getByRole("heading", { name: h })).toBeDefined();
    }
  });

  it("shows what an unlearned skill still rolls at, and stops once it is bought", () => {
    const { container } = renderTab({
      character: { derived: { totals: { AGI: 5 } } as never },
    });
    // the value side of the row, not the help tooltip on its name
    const value = container.querySelector(".skill-row.has-spec b") as HTMLElement;
    expect(value.textContent).toContain("デフォルト 4"); // AGI 5 − 1

    const bought = renderTab({
      character: {
        skills: { Blades: 3 },
        derived: { totals: { AGI: 5 }, skill_totals: { Blades: 3 } } as never,
      },
    });
    const boughtValue = bought.container.querySelector(".skill-row.has-spec b") as HTMLElement;
    expect(boughtValue.textContent).not.toContain("デフォルト");
    expect(boughtValue.textContent).toContain("3");
  });

  it("explains the terms behind a skill row: pool, specialization, defaulting, cap", () => {
    const { container } = renderTab();
    const button = container.querySelector(".skill-row.has-spec button") as HTMLElement;
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("判定ダイス = 技能レーティング + 関連能力値");
    expect(tip?.textContent).toContain("+2 ダイス");
    expect(tip?.textContent).toContain("戦闘技能／関連能力値 AGI／作成上限 6");
  });

  it("drops the −1 on a skill the Reflex Recorder covers, and says when defaulting is out", () => {
    const free = renderTab({
      character: {
        derived: { totals: { AGI: 5 }, no_default_penalty_skills: ["Blades"] } as never,
      },
    });
    expect(free.container.textContent).toContain("デフォルト 5（−1なし）");

    const blocked = renderTab({
      catalog: skillsCatalog({ skills: [{ ...blades, default: false }] }),
      character: { derived: { totals: { AGI: 5 } } as never },
    });
    expect(blocked.container.textContent).toContain("デフォルト不可");
  });

  it("gives the knowledge section the two defaulting pools, and Uneducated's cut", () => {
    const plain = renderTab({
      character: { derived: { totals: { INT: 4, LOG: 6 } } as never },
    });
    expect(plain.container.textContent).toContain("INT 3 ／ LOG 5");
    expect(plain.container.textContent).not.toContain("デフォルト不可");

    const uneducated = renderTab({
      character: {
        derived: {
          totals: { INT: 4, LOG: 6 },
          // Uneducated (SR5 p.80) also blocks an active category, which does
          // not belong on the knowledge line.
          blocked_default_categories: ["Academic", "Professional", "Technical Active"],
        } as never,
      },
    });
    const line = uneducated.container.textContent || "";
    expect(line).toContain("はデフォルト不可");
    expect(line).not.toContain("Technical Active");
  });

  it("commits an active-skill rating via patch on mouseUp", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter());
      return (
        <SkillsTab {...panelProps(ch, { catalog: skillsCatalog(), patch, setCharacter: setCh })} />
      );
    }
    render(<Harness />);
    // group slider is first, then the Blades active-skill slider
    const blade = screen.getAllByRole("slider")[1];
    fireEvent.change(blade, { target: { value: "4" } });
    fireEvent.mouseUp(blade);
    expect(patch).toHaveBeenCalledWith({ skills: { Blades: 4 } });
  });

  it("adds a custom knowledge skill with its category", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByPlaceholderText("カスタム知識名"), {
      target: { value: "Underworld" },
    });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));
    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { Underworld: 1 },
      native_languages: [],
      knowledge_categories: { Underworld: "Street" },
    });
  });

  it("adds a catalog knowledge skill from the picker", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ knowledge: [knowItem] }), patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Magic Theory"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ knowledge_skills: { "Magic Theory": 1 } }),
    );
  });

  const split = { levels: { Blades: 1 }, knowledge_levels: {}, karma: 8, knowledge_karma: 0 };

  it("lets a Priority creation mark skill levels as bought with karma", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        skills: { Blades: 4 },
        skill_karma: { Blades: 1 },
        knowledge_skills: { "Magic Theory": 2 },
        derived: {
          skill_totals: { Blades: 4 },
          skill_karma: split,
          knowledge_skills: [knowRow("Magic Theory", { rating: 2 })],
        } as never,
      },
    });
    const blades = screen.getByRole("spinbutton", {
      name: /Blades.*うちカルマ/,
    }) as HTMLInputElement;
    expect(blades.value).toBe("1");
    expect(blades.max).toBe("4");
    expect(screen.getByText("カルマで上げた技能：8 カルマ（知識技能 0 カルマ）")).toBeDefined();
    fireEvent.change(screen.getByRole("spinbutton", { name: /Magic Theory.*うちカルマ/ }), {
      target: { value: "1" },
    });
    expect(patch).toHaveBeenCalledWith({ knowledge_karma: { "Magic Theory": 1 } });
  });

  it("lets a skill group mark its top levels as bought with karma", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        skill_groups: { "Close Combat": 2 },
        skill_group_karma: { "Close Combat": 1 },
        derived: { skill_karma: { ...split, group_levels: { "Close Combat": 1 } } } as never,
      },
    });
    const group = screen.getByRole("spinbutton", {
      name: /Close Combat.*うちカルマ/,
    }) as HTMLInputElement;
    expect(group.value).toBe("1");
    expect(group.max).toBe("2");
    fireEvent.change(group, { target: { value: "2" } });
    expect(patch).toHaveBeenCalledWith({ skill_group_karma: { "Close Combat": 2 } });
  });

  it("offers no skill split in a Karma build or after creation", () => {
    for (const character of [
      {
        skills: { Blades: 4 },
        derived: { skill_karma: split, karma_chargen: { enabled: true } } as never,
      },
      { skills: { Blades: 4 }, career: true, derived: { skill_karma: split } as never },
    ]) {
      const { unmount } = renderTab({ character });
      expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
      unmount();
    }
  });

  it("explains a knowledge row's terms behind its help button", () => {
    const { container } = renderTab({
      character: {
        knowledge_skills: { "Magic Theory": 2 },
        derived: { knowledge_skills: [knowRow("Magic Theory", { rating: 2 })] } as never,
      },
    });
    const button = container.querySelector(".know-row button") as HTMLElement;
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("(INT + LOG) × 2");
  });

  it("says an exotic skill cannot be defaulted", () => {
    const { container } = renderTab({
      catalog: skillsCatalog({ skills: [blades, exoticSkill] }),
      character: {
        exotic_skills: [{ id: "e1", skill_name: "Exotic Ranged Weapon", extra: "", rating: 1 }],
        derived: {
          exotic_skills: [
            {
              id: "e1",
              skill_name: "Exotic Ranged Weapon",
              label: "Exotic Ranged Weapon",
              extra: "",
              attribute: "AGI",
              rating: 1,
              rating_max: 6,
            },
          ],
        } as never,
      },
    });
    const button = container.querySelector(".can-delete button") as HTMLElement;
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("デフォルトで振れない");
  });

  it("adds an exotic skill row via patch", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ skills: [blades, exoticSkill] }), patch });
    fireEvent.click(screen.getByRole("button", { name: /Exotic Ranged Weapon を追加/ }));
    expect(patch).toHaveBeenCalledWith({
      exotic_skills: [{ skill_name: "Exotic Ranged Weapon", extra: "", rating: 1 }],
    });
  });
});

describe("<SkillsTab> sliders", () => {
  it("commits a skill-group rating on blur as well as on mouseUp", () => {
    // a keyboard user never fires mouseUp; without the blur handler their
    // edit is dropped on the way out of the control
    const patch = vi.fn();
    renderStateful(patch);

    const group = screen.getAllByRole("slider")[0];
    fireEvent.change(group, { target: { value: "3" } });
    // focusOut, not blur: React maps onBlur onto the bubbling focusout event,
    // and a non-bubbling `blur` never reaches the handler
    fireEvent.focusOut(group);

    expect(patch).toHaveBeenCalledWith({ skill_groups: { "Close Combat": 3 } });
  });

  it("lets a skill with a max bonus go past the normal ceiling", () => {
    renderTab({
      character: {
        derived: { skill_rating_max: 6, skill_max_bonus: { Blades: 1 } },
      } as never,
    });

    expect(screen.getAllByRole("slider")[1].getAttribute("max")).toBe("7");
  });
});

describe("active skill ordering", () => {
  const pistols = { ...blades, id: "pistols", name: "Pistols", skillgroup: "Firearms" };
  const computer = {
    ...blades,
    id: "computer",
    name: "Computer",
    category: "Technical Active",
    skillgroup: "Electronics",
  };
  const con = {
    ...blades,
    id: "con",
    name: "Con",
    category: "Social Active",
    skillgroup: "Acting",
  };

  /** The tab renders one heading per category and the rows under it, so the
   *  skill names in document order are the on-screen order. */
  function namesInOrder(container: HTMLElement): string[] {
    return [
      ...container.querySelectorAll(".skill-row.has-spec > span:first-child .help-tip-label"),
    ].map((el) => el.textContent || "");
  }

  it("groups by category in the rulebook's order, whatever order the catalog is in", () => {
    // catalog order here mimics the vendored file: Technical first, Combat late
    const { container } = renderTab({
      catalog: skillsCatalog({
        skills: [computer, con, pistols, blades],
        active_categories: [
          "Combat Active",
          "Physical Active",
          "Social Active",
          "Magical Active",
          "Resonance Active",
          "Technical Active",
          "Vehicle Active",
        ],
      }),
    });

    expect(namesInOrder(container)).toEqual(["Blades", "Pistols", "Con", "Computer"]);
    const headings = [...container.querySelectorAll(".skill-cat")].map((el) => el.textContent);
    expect(headings).toEqual(["戦闘技能", "対人技能", "技術技能"]);
  });

  it("falls back to the rulebook order when the catalog predates active_categories", () => {
    const { container } = renderTab({
      catalog: skillsCatalog({ skills: [computer, con, blades] }),
    });
    expect(namesInOrder(container)).toEqual(["Blades", "Con", "Computer"]);
  });

  it("sorts skill groups the way the catalog hands them over", () => {
    const { container } = renderTab({
      catalog: skillsCatalog({
        groups: ["Close Combat", "Electronics", "Engineering"],
        skills: [blades],
      }),
    });
    const groups = [...container.querySelectorAll(".skill-row:not(.has-spec) > span:first-child")];
    expect(groups.map((el) => el.textContent)).toEqual([
      "Close Combat",
      "Electronics",
      "Engineering",
    ]);
  });
});

/**
 * A skill you do not buy but have to *name*: a quality's pick, a piece of
 * ware's, an adept power's. Each has a control next to what grants it, on
 * that thing's own tab — and nothing here said so, which is where a player
 * looks for a skill. The picks are repeated here, and writing to one has to
 * reach the right list: `skill_picks` for a quality or ware, `adept_powers`
 * for a power whose `extra` *is* the skill.
 */
describe("<SkillsTab> skills that come with something", () => {
  const slot = (over: Record<string, unknown> = {}) => ({
    key: "quality:q1:0",
    source: "College Education",
    source_kind: "quality",
    source_id: "q1",
    picked: "",
    bonus: 0,
    max: 0,
    rating: 0,
    options: ["Blades", "Pistols"],
    knowledgeskills: false,
    ...over,
  });

  const power = (over: Record<string, unknown> = {}) => ({
    id: "p1",
    power_id: "c-p1",
    name: "Improved Ability (Combat)",
    rating: 1,
    rating_min: 1,
    rating_max: 6,
    extra: "",
    cost: 0.5,
    select: "skill",
    options: ["Blades", "Pistols"],
    ...over,
  });

  it("says nothing when the character has no such skill", () => {
    renderTab();
    expect(screen.queryByText("ついてくる技能")).toBeNull();
  });

  it("writes a quality's pick to skill_picks", () => {
    const patch = vi.fn();
    renderTab({
      character: { derived: { skill_pick_slots: [slot()] } } as never,
      patch,
    });

    fireEvent.change(screen.getByRole("combobox", { name: /College Education/ }), {
      target: { value: "Blades" },
    });

    expect(patch).toHaveBeenCalledWith({ skill_picks: { "quality:q1:0": "Blades" } });
  });

  it("writes an adept power's skill to the power, not to skill_picks", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        adept_powers: [{ id: "p1", power_id: "c-p1", rating: 1, extra: "" }],
        derived: { adept_powers: [power()] },
      } as never,
      patch,
    });

    fireEvent.change(screen.getByRole("combobox", { name: /Improved Ability/ }), {
      target: { value: "Pistols" },
    });

    expect(patch).toHaveBeenCalledWith({
      adept_powers: [{ id: "p1", power_id: "c-p1", rating: 1, extra: "Pistols" }],
    });
  });

  it("writes a mentor's power target to mentor_extras", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        derived: {
          mentor: {
            id: "m1",
            name: "Bear",
            advantage: "",
            disadvantage: "",
            choices: [
              {
                name: "Bear (Combat)",
                set: "",
                audience: "all",
                selected: true,
                extra: "",
                extra_options: [],
                power_targets: [
                  {
                    power: "Improved Ability (Combat)",
                    key: "Bear (Combat)|Improved Ability (Combat)",
                    kind: "skill",
                    extra: "",
                    options: ["Blades", "Pistols"],
                  },
                ],
              },
            ],
          },
        },
      } as never,
      patch,
    });

    fireEvent.change(screen.getByRole("combobox", { name: /Improved Ability/ }), {
      target: { value: "Blades" },
    });

    expect(patch).toHaveBeenCalledWith({
      mentor_extras: { "Bear (Combat)|Improved Ability (Combat)": "Blades" },
    });
  });

  // An offered choice the character did not take grants nothing, so it asks
  // for nothing here either.
  it("leaves a mentor choice the character did not take alone", () => {
    renderTab({
      character: {
        derived: {
          mentor: {
            id: "m1",
            name: "Bear",
            advantage: "",
            disadvantage: "",
            choices: [
              {
                name: "Bear (Combat)",
                set: "",
                audience: "all",
                selected: false,
                extra: "",
                extra_options: [],
                power_targets: [
                  {
                    power: "Improved Ability (Combat)",
                    key: "k",
                    kind: "skill",
                    extra: "",
                    options: ["Blades"],
                  },
                ],
              },
            ],
          },
        },
      } as never,
    });
    expect(screen.queryByText("ついてくる技能")).toBeNull();
  });

  // A free power's target is not the player's to set: the choice that granted
  // it already named one, and the adept tab hides the select for that reason.
  it("leaves a power that came with its target already named alone", () => {
    renderTab({
      character: { derived: { adept_powers: [power({ free_only: true })] } } as never,
    });
    expect(screen.queryByText("ついてくる技能")).toBeNull();
  });
});
