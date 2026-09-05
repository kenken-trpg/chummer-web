import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { QualityExtraEditor } from "./QualityExtraEditor";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Each branch of this component renders a control whose only visible cue is a
 * placeholder option. A quality list with several of these used to announce
 * "combobox" over and over; the assertion here is by accessible name, so a
 * dropped label fails instead of passing silently.
 */
function renderFor(q: Record<string, unknown>, over: Record<string, unknown> = {}) {
  const ch = makeCharacter();
  render(
    <QualityExtraEditor
      q={{ id: "q1", name: "Allergy", ...q } as any}
      ch={ch}
      d={{ ...ch.derived, ...(over.d as object) }}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={vi.fn()}
      setCharacter={vi.fn()}
      catalog={makeCatalog((over.catalog as any) ?? {})}
      catalogById={new Map()}
    />,
  );
}

describe("<QualityExtraEditor> accessible names", () => {
  it("names a free-text target after its quality", () => {
    renderFor({ needs_extra: true });
    expect(screen.getByRole("textbox", { name: "Allergy: 対象" })).toBeDefined();
  });

  it("names both halves of a select-or-type target", () => {
    renderFor({ needs_extra: true, select_options: ["Pollen", "Sunlight"] });
    expect(screen.getByRole("combobox", { name: "Allergy: 対象を選択" })).toBeDefined();
    expect(screen.getByRole("textbox", { name: "Allergy: 対象を手入力" })).toBeDefined();
  });

  it("names the left/right picker", () => {
    renderFor({ name: "Cyber Snob", selectside: true });
    expect(screen.getByRole("combobox", { name: "Cyber Snob: 左右を選択" })).toBeDefined();
  });

  it("names an attribute picker", () => {
    renderFor({ name: "Exceptional Attribute" });
    expect(
      screen.getByRole("combobox", { name: "Exceptional Attribute: 能力値を選択" }),
    ).toBeDefined();
  });

  it("names a skill-group picker", () => {
    renderFor(
      { name: "Aptitude", extra_kind: "skillgroup" },
      { catalog: { skills: { skills: [], groups: ["Stealth"], knowledge: [] } } },
    );
    expect(screen.getByRole("combobox", { name: "Aptitude: 技能グループを選択" })).toBeDefined();
  });

  it("names both selects of the spell + spirit pair", () => {
    renderFor({
      name: "Focused Concentration",
      extra_kind: "spell_spirit_category",
      select_options: ["Combat"],
      spirit_options: ["Spirit of Fire"],
    });
    expect(
      screen.getByRole("combobox", { name: "Focused Concentration: 呪文カテゴリを選択" }),
    ).toBeDefined();
    expect(
      screen.getByRole("combobox", { name: "Focused Concentration: 精霊を選択" }),
    ).toBeDefined();
  });

  it("numbers the slots when a quality grants more than one spirit", () => {
    renderFor(
      { name: "Mentor Spirit", extra_kind: "add_spirit", add_spirit_count: 2 },
      { catalog: { spirits: [{ name: "Spirit of Air" }] as any } },
    );
    expect(screen.getByRole("combobox", { name: "Mentor Spirit: 追加精霊 1を選択" })).toBeDefined();
    expect(screen.getByRole("combobox", { name: "Mentor Spirit: 追加精霊 2を選択" })).toBeDefined();
  });

  it("names the two Black Market Pipeline pickers apart", () => {
    renderFor({ name: "Black Market Pipeline" });
    expect(
      screen.getByRole("combobox", { name: "Black Market Pipeline: 商品カテゴリを選択" }),
    ).toBeDefined();
    expect(
      screen.getByRole("combobox", { name: "Black Market Pipeline: コンタクトを選択" }),
    ).toBeDefined();
  });

  it("renders nothing for a quality that takes no target", () => {
    const { container } = render(
      <QualityExtraEditor
        q={{ id: "q1", name: "Toughness" } as any}
        ch={makeCharacter()}
        d={makeCharacter().derived}
        tr={identityTr}
        trGroup={identityTr}
        t={(k) => k}
        ui={testUi}
        patch={vi.fn()}
        setCharacter={vi.fn()}
        catalog={makeCatalog()}
        catalogById={new Map()}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});

/**
 * What the controls above actually do.
 *
 * Every branch writes into one shared bag, `ch.quality_extras`, keyed by the
 * quality's id — and three branches need *two* values for one quality, so
 * they mint a second key by hand (`${id}:contact`, `${id}:spiritcategory`,
 * `${id}:addspirit:N`). A branch that writes to the wrong key loses the
 * value silently: the control re-renders empty and the engine sees nothing.
 * These tests assert the key, not just that a patch happened.
 *
 * The select-plus-type pairs have a second rule worth pinning. The select
 * shows the current value only when it is one of its options; a value typed
 * by hand leaves the select blank rather than making it display some other
 * option. And the input drafts through `setCharacter` on every keystroke and
 * only commits on blur — a patch per keystroke would be a round trip per
 * keystroke.
 */
function editorFor(q: Record<string, unknown>, over: Record<string, unknown> = {}) {
  const patch = vi.fn();
  const setCharacter = vi.fn();
  const ch = makeCharacter((over.ch as any) ?? {});
  render(
    <QualityExtraEditor
      q={{ id: "q1", name: "Allergy", ...q } as any}
      ch={ch}
      d={{ ...ch.derived, ...(over.d as object) }}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={setCharacter}
      catalog={makeCatalog((over.catalog as any) ?? {})}
      catalogById={(over.catalogById as any) ?? new Map()}
    />,
  );
  return { patch, setCharacter, ch };
}

describe("<QualityExtraEditor> what each control writes", () => {
  it("a free-text target drafts on every keystroke without a round trip", () => {
    const { patch, setCharacter } = editorFor({ needs_extra: true });

    fireEvent.change(screen.getByRole("textbox", { name: "Allergy: 対象" }), {
      target: { value: "Pollen" },
    });

    expect(patch).not.toHaveBeenCalled(); // otherwise: one request per keystroke
    expect(setCharacter.mock.calls[0][0].quality_extras).toEqual({ q1: "Pollen" });
  });

  it("a free-text target commits what is in the field on blur", () => {
    // the value has to come from the character: the input is controlled, so
    // a draft that never reached `ch` is not in the field to commit
    const { patch } = editorFor(
      { needs_extra: true },
      { ch: { quality_extras: { q1: "Pollen" } } },
    );

    fireEvent.focusOut(screen.getByRole("textbox", { name: "Allergy: 対象" }));

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Pollen" } });
  });

  it("keeps the other qualities' targets when it writes its own", () => {
    // the bag is shared: replacing it rather than spreading it wipes every
    // other quality's target in one patch
    const { patch } = editorFor(
      { needs_extra: true, select_options: ["Pollen", "Sunlight"] },
      { ch: { quality_extras: { other: "Gold" } } },
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Allergy: 対象を選択" }), {
      target: { value: "Pollen" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { other: "Gold", q1: "Pollen" } });
  });

  it("leaves the select blank for a value that was typed, not picked", () => {
    // `known.includes(current) ? current : ""` is defensive rather than load-
    // bearing -- a select whose value matches no option renders blank either
    // way -- but it keeps the intent readable, and this pins the behaviour
    editorFor(
      { needs_extra: true, select_options: ["Pollen", "Sunlight"] },
      { ch: { quality_extras: { q1: "Soy" } } },
    );

    expect(
      (screen.getByRole("combobox", { name: "Allergy: 対象を選択" }) as HTMLSelectElement).value,
    ).toBe("");
    expect(
      (screen.getByRole("textbox", { name: "Allergy: 対象を手入力" }) as HTMLInputElement).value,
    ).toBe("Soy");
  });

  it("takes its options from the catalog entry when the row carries none", () => {
    // an imported character's quality row is thinner than the catalog's
    editorFor(
      { needs_extra: true },
      { catalogById: new Map([["q1", { extra_kind: "text", select_options: ["Pollen"] }]]) },
    );

    const select = screen.getByRole("combobox", { name: "Allergy: 対象を選択" });
    expect([...select.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "対象を選択",
      "Pollen",
    ]);
  });

  it("writes the side a one-sided quality is on", () => {
    const { patch } = editorFor({ name: "Missing Limb", selectside: true });

    fireEvent.change(screen.getByRole("combobox", { name: "Missing Limb: 左右を選択" }), {
      target: { value: "Right" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Right" } });
  });

  it("offers only the attributes Exceptional Attribute can apply to", () => {
    const { patch } = editorFor({ name: "Exceptional Attribute" });

    const select = screen.getByRole("combobox", { name: "Exceptional Attribute: 能力値を選択" });
    const values = [...select.querySelectorAll("option")].map(
      (o) => (o as HTMLOptionElement).value,
    );
    // EDG, MAG and RES have their own rules and are not on offer here
    expect(values).toEqual(["", "BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA"]);

    fireEvent.change(select, { target: { value: "LOG" } });
    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "LOG" } });
  });

  it("writes the skill group a quality attaches to", () => {
    const { patch } = editorFor(
      { name: "Aptitude", extra_kind: "skillgroup" },
      { catalog: { skills: { skills: [], groups: ["Firearms", "Close Combat"], knowledge: [] } } },
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Aptitude: 技能グループを選択" }), {
      target: { value: "Firearms" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Firearms" } });
  });

  it("falls back to the skill's own specialisations for an expertise", () => {
    const { patch } = editorFor(
      { name: "Aptitude", extra_kind: "expertise", expertise_skill: "Blades" },
      {
        catalog: {
          skills: {
            skills: [{ id: "s1", name: "Blades", specs: ["Swords"] }],
            groups: [],
            knowledge: [],
          },
        },
      },
    );

    const select = screen.getByRole("combobox", { name: "Aptitude: Blades の Expertise を選択" });
    expect([...select.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "Blades の Expertise を選択",
      "Swords",
    ]);

    fireEvent.change(select, { target: { value: "Swords" } });
    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Swords" } });
  });

  it("names an expertise picker that has no skill to name", () => {
    editorFor({ name: "Aptitude", extra_kind: "expertise" });
    expect(screen.getByRole("combobox", { name: "Aptitude: Expertise を選択" })).toBeDefined();
  });

  it("lets a matrix action be typed when the catalog list falls short", () => {
    const q = {
      name: "Codeslinger",
      extra_kind: "matrix_action",
      select_options: ["Hack on the Fly"],
    };
    const { setCharacter } = editorFor(q);
    fireEvent.change(
      screen.getByRole("textbox", { name: "Codeslinger: マトリクスアクションを手入力" }),
      { target: { value: "Spoof Command" } },
    );
    expect(setCharacter.mock.calls[0][0].quality_extras).toEqual({ q1: "Spoof Command" });

    cleanup();
    const { patch } = editorFor(q, { ch: { quality_extras: { q1: "Spoof Command" } } });
    fireEvent.focusOut(
      screen.getByRole("textbox", { name: "Codeslinger: マトリクスアクションを手入力" }),
    );
    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Spoof Command" } });
  });

  it("keeps the spell and the spirit of a paired quality under separate keys", () => {
    // one key would make choosing a spirit overwrite the spell category
    const { patch } = editorFor({
      name: "Focused Concentration",
      extra_kind: "spell_spirit_category",
      select_options: ["Combat"],
      spirit_options: ["Spirit of Fire"],
    });

    fireEvent.change(
      screen.getByRole("combobox", { name: "Focused Concentration: 呪文カテゴリを選択" }),
      { target: { value: "Combat" } },
    );
    fireEvent.change(screen.getByRole("combobox", { name: "Focused Concentration: 精霊を選択" }), {
      target: { value: "Spirit of Fire" },
    });

    expect(patch.mock.calls[0][0]).toEqual({ quality_extras: { q1: "Combat" } });
    expect(patch.mock.calls[1][0]).toEqual({
      quality_extras: { "q1:spiritcategory": "Spirit of Fire" },
    });
  });

  it("a spirit-only quality uses the plain key and shows no spell picker", () => {
    const { patch } = editorFor({
      name: "Spirit Affinity",
      extra_kind: "spirit_category",
      spirit_options: ["Spirit of Air"],
    });

    expect(screen.queryByRole("combobox", { name: /呪文カテゴリ/ })).toBeNull();
    fireEvent.change(screen.getByRole("combobox", { name: "Spirit Affinity: 精霊を選択" }), {
      target: { value: "Spirit of Air" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Spirit of Air" } });
  });

  it("a spell-only quality shows no spirit picker", () => {
    editorFor({
      name: "Focused Concentration",
      extra_kind: "spell_category",
      select_options: ["Combat"],
    });

    expect(screen.getByRole("combobox", { name: /呪文カテゴリ/ })).toBeDefined();
    expect(screen.queryByRole("combobox", { name: /精霊を選択/ })).toBeNull();
  });

  it("numbers the add-spirit keys so two slots do not share one", () => {
    const { patch } = editorFor(
      { name: "Mentor Spirit", extra_kind: "add_spirit", add_spirit_count: 2 },
      { catalog: { spirits: [{ name: "Spirit of Man" }, { name: "Homunculus" }] } },
    );

    const first = screen.getByRole("combobox", { name: "Mentor Spirit: 追加精霊 1を選択" });
    // Homunculus is never a bound spirit choice
    expect([...first.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "追加精霊 1を選択",
      "Spirit of Man",
    ]);

    fireEvent.change(screen.getByRole("combobox", { name: "Mentor Spirit: 追加精霊 2を選択" }), {
      target: { value: "Spirit of Man" },
    });
    expect(patch).toHaveBeenCalledWith({
      quality_extras: { "q1:addspirit:1": "Spirit of Man" },
    });
  });

  it("prefers the engine's own add-spirit slots when it sent some", () => {
    const { patch } = editorFor(
      { name: "Mentor Spirit", extra_kind: "add_spirit" },
      {
        d: {
          add_spirit_picks: [
            { quality_id: "q1", index: 0, key: "q1:slot", value: "", options: ["Spirit of Fire"] },
          ],
        },
      },
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Mentor Spirit: 追加精霊を選択" }), {
      target: { value: "Spirit of Fire" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { "q1:slot": "Spirit of Fire" } });
  });

  it("Black Market Pipeline stores the contact apart from the category", () => {
    const { patch } = editorFor(
      { name: "Black Market Pipeline" },
      {
        d: {
          contacts: [{ id: "k1", name: "Fixer", role: "Fixer", connection: 3, loyalty: 2 }],
          black_market_avail_bonus: 2,
        },
      },
    );

    fireEvent.change(
      screen.getByRole("combobox", { name: "Black Market Pipeline: 商品カテゴリを選択" }),
      { target: { value: "Cyberware" } },
    );
    fireEvent.change(
      screen.getByRole("combobox", { name: "Black Market Pipeline: コンタクトを選択" }),
      { target: { value: "k1" } },
    );

    expect(patch.mock.calls[0][0]).toEqual({ quality_extras: { q1: "Cyberware" } });
    expect(patch.mock.calls[1][0]).toEqual({ quality_extras: { "q1:contact": "k1" } });
    expect(screen.getByText(/入手判定 \+2/)).toBeDefined();
  });

  it("names an unnamed contact rather than offering a blank row", () => {
    editorFor(
      { name: "Black Market Pipeline" },
      { d: { contacts: [{ id: "k1", name: "", connection: 1, loyalty: 1 }] } },
    );

    const select = screen.getByRole("combobox", {
      name: "Black Market Pipeline: コンタクトを選択",
    });
    expect(select.textContent).toContain("（無名）");
  });

  it("writes the weapon skill a quality is tied to", () => {
    const { patch } = editorFor({
      name: "Quick Draw",
      extra_kind: "weapon_skill",
      select_options: ["Pistols"],
    });

    fireEvent.change(screen.getByRole("combobox", { name: "Quick Draw: 技能を選択" }), {
      target: { value: "Pistols" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Pistols" } });
  });

  it("writes the quality another quality hangs off", () => {
    const { patch } = editorFor({
      name: "Prejudiced",
      extra_kind: "quality",
      select_options: ["Elf"],
    });

    fireEvent.change(screen.getByRole("combobox", { name: "Prejudiced: 付帯資質を選択" }), {
      target: { value: "Elf" },
    });

    expect(patch).toHaveBeenCalledWith({ quality_extras: { q1: "Elf" } });
  });
});
