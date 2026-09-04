import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
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
      t={(k) => k}
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
        t={(k) => k}
        patch={vi.fn()}
        setCharacter={vi.fn()}
        catalog={makeCatalog()}
        catalogById={new Map()}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
