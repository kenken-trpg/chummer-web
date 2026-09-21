import { screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import {
  knowItem,
  skillsCatalog,
  renderTab,
  renderStateful,
  knowRow,
  language,
} from "./SkillsTab.helpers";

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

describe("<SkillsTab> knowledge skills", () => {
  it("does not add a skill the character already has, or a blank name", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        knowledge_skills: { Underworld: 2 },
        derived: { knowledge_skills: [knowRow("Underworld", { rating: 2 })] },
      } as never,
    });

    const name = screen.getByPlaceholderText("カスタム知識名");
    fireEvent.change(name, { target: { value: "  " } });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));
    // whitespace trims to nothing; a duplicate would silently reset it to 1
    fireEvent.change(name, { target: { value: " Underworld " } });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));

    expect(patch).not.toHaveBeenCalled();
    // and the name stays in the box to be corrected, rather than vanishing
    expect((name as HTMLInputElement).value).toBe(" Underworld ");
  });

  it("clears the name box once a custom skill is added", () => {
    renderTab();
    const name = screen.getByPlaceholderText("カスタム知識名") as HTMLInputElement;
    fireEvent.change(name, { target: { value: "Underworld" } });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));
    expect(name.value).toBe("");
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
      } as never,
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
      } as never,
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
      } as never,
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
      } as never,
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
      } as never,
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
      } as never,
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
    } as never);

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
        // a supplement entry: on the list unless the settings drop its book
        { name: "Aztechnology Politics", category: "Professional", attribute: "LOG", source: "SG" },
      ],
    });
  const listed = () =>
    [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

  // It used to list SR5 entries only whatever the settings said, so a book
  // the GM had enabled looked like one this app did not have.
  it("lists every entry the settings allow, and searches within it", () => {
    renderTab({ catalog: catalog() });
    expect(listed()).toEqual(["Magic Theory", "Street Gangs", "Aztechnology Politics"]);

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
    expect(listed()).toEqual(["Magic Theory", "Street Gangs", "Aztechnology Politics"]);
  });

  it("hides what the character already has", () => {
    renderTab({
      catalog: catalog(),
      character: {
        knowledge_skills: { "Magic Theory": 1 },
        derived: { knowledge_skills: [knowRow("Magic Theory")] },
      } as never,
    });

    expect(listed()).toEqual(["Street Gangs", "Aztechnology Politics"]);
  });
});
