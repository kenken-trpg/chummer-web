import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const blades = {
  id: "blades",
  name: "Blades",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: "Close Combat",
  source: "SR5",
  specs: ["Swords"],
};
const exoticSkill = {
  id: "exranged",
  name: "Exotic Ranged Weapon",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: null,
  source: "SR5",
  exotic: true,
};
const knowItem = {
  name: "Magic Theory",
  category: "Academic",
  attribute: "LOG",
  source: "SR5",
};

function skillsCatalog(over: Record<string, unknown> = {}) {
  return makeCatalog({
    skills: { groups: ["Close Combat"], skills: [blades], knowledge: [], ...over },
  } as any);
}

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
    setCharacter?: (c: Character) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <SkillsTab
      catalog={over.catalog ?? skillsCatalog()}
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

/**
 * The sliders are controlled inputs whose value comes from `character`, so a
 * `fireEvent.change` against a static render is reverted by React before the
 * commit handler ever reads it — the handler sees the old value and the test
 * passes for the wrong reason, or fails for a reason that is not a bug. Any
 * test that changes a slider and then commits has to hold real state.
 */
function renderStateful(
  patch: (b: Record<string, unknown>) => void,
  init: Parameters<typeof makeCharacter>[0] = {},
  catalog = skillsCatalog(),
) {
  function Harness() {
    const [ch, setCh] = useState<Character>(() => makeCharacter(init));
    return (
      <SkillsTab
        catalog={catalog}
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
  return render(<Harness />);
}

describe("<SkillsTab>", () => {
  it("renders the point line and the four sections", () => {
    renderTab();
    expect(screen.getByText(/技能 0\/0 ・ グループ 0\/0 ・ 知識 0\/0/)).toBeDefined();
    for (const h of ["技能グループ", "アクティブ技能", "Exotic技能", "知識技能"]) {
      expect(screen.getByRole("heading", { name: h })).toBeDefined();
    }
  });

  it("commits an active-skill rating via patch on mouseUp", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter());
      return (
        <SkillsTab
          catalog={skillsCatalog()}
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

  it("adds an exotic skill row via patch", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ skills: [blades, exoticSkill] }), patch });
    fireEvent.click(screen.getByRole("button", { name: /Exotic Ranged Weapon を追加/ }));
    expect(patch).toHaveBeenCalledWith({
      exotic_skills: [{ skill_name: "Exotic Ranged Weapon", extra: "", rating: 1 }],
    });
  });
});

/**
 * Everything below covers the half of this tab that edits a character rather
 * than displaying one. The knowledge section is the interesting part: a single
 * knowledge skill's state is spread across **four** character fields —
 * `knowledge_skills`, `native_languages`, `knowledge_categories` and
 * `skill_specializations` — and the tab is what keeps them agreeing. A patch
 * that updates three of the four leaves a rating with no skill, or a
 * specialisation of something the character no longer has, and neither shows
 * up on screen.
 *
 * `patchKnowledge()` exists for exactly that reason: it resends all three of
 * its fields on every edit. So these tests assert the **whole** patch body,
 * not just the field being edited.
 */

/** A derived knowledge row, shaped as `d.knowledge_skills` delivers it. */
const knowRow = (name: string, over: Record<string, unknown> = {}) => ({
  name,
  category: "Academic",
  attribute: "LOG",
  rating: 1,
  native: false,
  ...over,
});

const language = (name: string, over: Record<string, unknown> = {}) =>
  knowRow(name, { category: "Language", ...over });

describe("<SkillsTab> knowledge skills", () => {
  it("does not add a skill the character already has, or a blank name", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Underworld: 2 },
        derived: { knowledge_skills: [knowRow("Underworld", { rating: 2 })] },
      } as any,
    });

    const name = screen.getByPlaceholderText("カスタム知識名");
    fireEvent.change(name, { target: { value: "  " } });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));
    // whitespace trims to nothing; a duplicate would silently reset it to 1
    fireEvent.change(name, { target: { value: " Underworld " } });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));

    expect(patch).not.toHaveBeenCalled();
  });

  it("records a category only for a skill the catalog does not already place", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ knowledge: [knowItem] }), patch });

    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Magic Theory"),
    )!;
    fireEvent.click(row.querySelector("button")!);

    // the catalog says Academic; storing it again would let the two disagree
    // after a data update
    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { "Magic Theory": 1 },
      native_languages: [],
      knowledge_categories: {},
    });
  });

  it("marking a language native drops its rating — a native language is free", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Japanese: 3 },
        derived: {
          knowledge_skills: [language("Japanese", { rating: 3 })],
          native_language_limit: 1,
        },
      } as any,
    });

    fireEvent.click(screen.getByRole("checkbox"));

    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: {},
      native_languages: ["Japanese"],
      knowledge_categories: {},
    });
  });

  it("past the native limit the oldest native comes back as a rated skill", () => {
    // Bilingual raises the limit; without it a second native has to displace
    // the first, and the displaced one must not vanish
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Japanese: 2 },
        native_languages: ["English"],
        derived: {
          knowledge_skills: [
            language("English", { native: true }),
            language("Japanese", { rating: 2 }),
          ],
          native_language_limit: 1,
        },
      } as any,
    });

    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { English: 1 }, // pushed out, back at rating 1
      native_languages: ["Japanese"],
      knowledge_categories: {},
    });
  });

  it("keeps both natives when the character is allowed two", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Japanese: 2 },
        native_languages: ["English"],
        derived: {
          knowledge_skills: [
            language("English", { native: true }),
            language("Japanese", { rating: 2 }),
          ],
          native_language_limit: 2,
        },
      } as any,
    });

    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    expect(patch.mock.calls[0][0].native_languages).toEqual(["English", "Japanese"]);
    expect(patch.mock.calls[0][0].knowledge_skills).toEqual({});
  });

  it("un-marking a native gives the language a rating back", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: {},
        native_languages: ["English"],
        derived: { knowledge_skills: [language("English", { native: true })] },
      } as any,
    });

    fireEvent.click(screen.getByRole("checkbox"));

    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { English: 1 },
      native_languages: [],
      knowledge_categories: {},
    });
  });

  it("removing a skill clears its rating, native flag, category and spec at once", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Sperethiel: 3, Underworld: 2 },
        native_languages: ["Sperethiel"],
        knowledge_categories: { Sperethiel: "Language", Underworld: "Street" },
        skill_specializations: { Sperethiel: "Poetry", Underworld: "Gangs" },
        derived: {
          knowledge_skills: [
            language("Sperethiel", { rating: 3 }),
            knowRow("Underworld", { category: "Street", rating: 2 }),
          ],
        },
      } as any,
    });

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    // a leftover in any one of the four is a row that renders nowhere
    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { Underworld: 2 },
      native_languages: [],
      knowledge_categories: { Underworld: "Street" },
      skill_specializations: { Underworld: "Gangs" },
    });
  });

  it("only a custom skill lets you change its category", () => {
    const patch = vi.fn();
    renderTab({
      catalog: skillsCatalog({ knowledge: [knowItem] }),
      patch,
      character: {
        knowledge_skills: { "Magic Theory": 1, Underworld: 1 },
        derived: {
          knowledge_skills: [
            knowRow("Magic Theory"),
            knowRow("Underworld", { category: "Street" }),
          ],
        },
      } as any,
    });

    // one select, not two: the catalog skill shows its category as text
    const selects = screen.getAllByRole("combobox");
    const catSelect = selects.find((el) =>
      [...el.querySelectorAll("option")].some((o) => o.textContent === "街"),
    )!;
    fireEvent.change(catSelect, { target: { value: "Academic" } });

    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { "Magic Theory": 1, Underworld: 1 },
      native_languages: [],
      knowledge_categories: { Underworld: "Academic" },
    });
  });

  it("commits a knowledge rating on blur", () => {
    const patch = vi.fn();
    renderStateful(patch, {
      knowledge_skills: { Underworld: 1 },
      derived: { knowledge_skills: [knowRow("Underworld", { category: "Street" })] },
    } as any);

    const slider = screen.getAllByRole("slider").at(-1)!;
    fireEvent.change(slider, { target: { value: "4" } });
    fireEvent.focusOut(slider);

    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ knowledge_skills: { Underworld: 4 } }),
    );
  });
});

describe("<SkillsTab> the knowledge picker", () => {
  const catalog = () =>
    skillsCatalog({
      knowledge: [
        knowItem, // Magic Theory / Academic / SR5
        { name: "Street Gangs", category: "Street", attribute: "INT", source: "SR5" },
        // a supplement entry: off the list until you search for it
        { name: "Aztechnology Politics", category: "Professional", attribute: "LOG", source: "SG" },
      ],
    });
  const listed = () =>
    [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

  it("lists core entries only until the search box has something in it", () => {
    renderTab({ catalog: catalog() });
    expect(listed()).toEqual(["Magic Theory", "Street Gangs"]);

    fireEvent.change(screen.getByPlaceholderText("知識技能を検索"), {
      target: { value: "aztech" },
    });
    expect(listed()).toEqual(["Aztechnology Politics"]);
  });

  it("a category tab narrows the list, and すべて puts it back", () => {
    renderTab({ catalog: catalog() });

    fireEvent.click(screen.getByRole("button", { name: "街" }));
    expect(listed()).toEqual(["Street Gangs"]);

    fireEvent.click(screen.getByRole("button", { name: "すべて" }));
    expect(listed()).toEqual(["Magic Theory", "Street Gangs"]);
  });

  it("hides what the character already has", () => {
    renderTab({
      catalog: catalog(),
      character: {
        knowledge_skills: { "Magic Theory": 1 },
        derived: { knowledge_skills: [knowRow("Magic Theory")] },
      } as any,
    });

    expect(listed()).toEqual(["Street Gangs"]);
  });
});

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
      } as any,
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
    rerender(
      <SkillsTab
        catalog={skillsCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        trGroup={identityTr}
        t={(k) => k}
        ui={testUi}
        patch={() => {}}
        setCharacter={() => {}}
      />,
    );
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
      } as any,
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
      { exotic_skills: rows, derived: { exotic_skills: rows } } as any,
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
      } as any,
    });

    expect(screen.getAllByRole("slider")[1].getAttribute("max")).toBe("7");
  });
});
