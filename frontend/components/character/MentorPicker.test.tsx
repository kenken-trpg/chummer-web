import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BooksProvider } from "@/lib/character/books";
import { MentorPicker } from "./MentorPicker";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import type { MentorInfo } from "@/lib/types";

const CHOICE = "Adept: 2 free levels of Improved Potential";
const TARGET_KEY = `${CHOICE} / Improved Potential (Chaos Mentor)`;

const chaos: MentorInfo = {
  id: "chaos",
  name: "Chaos",
  source: "SG",
  choices: [
    {
      name: CHOICE,
      set: "",
      audience: "adept",
      selected: true,
      extra: "Improved Potential (Physical)",
      extra_options: ["Improved Potential (Physical)", "Improved Potential (Mental)"],
      power_targets: [
        {
          power: "Improved Potential (Chaos Mentor)",
          key: TARGET_KEY,
          kind: "limit",
          extra: "",
          options: ["Physical", "Mental", "Social"],
        },
      ],
    },
  ],
};

function renderPicker(onPatch = vi.fn(), tr: (name: string) => string = (n) => n) {
  const ch = makeCharacter({ mentor_id: "chaos", mentor_choices: [CHOICE] });
  render(
    <MentorPicker
      catalog={makeCatalog({
        mentors: [{ id: "chaos", name: "Chaos", source: "SG", page: "200" }],
      })}
      mentor={chaos}
      ch={ch}
      tr={tr}
      onPatch={onPatch}
    />,
  );
  return onPatch;
}

describe("MentorPicker", () => {
  // The mentor list never applied the settings' book list, so a Street
  // Grimoire mentor stayed on offer with SG switched off.
  it("narrows the list to the enabled books, but keeps the current pick", () => {
    const catalog = makeCatalog({
      mentors: [
        { id: "chaos", name: "Chaos", source: "SG", page: "200" },
        { id: "bear", name: "Bear", source: "SR5", page: "394" },
      ],
    });
    const picker = (mentorId: string) => (
      <BooksProvider books={["SR5"]}>
        <MentorPicker
          catalog={catalog}
          mentor={mentorId === "chaos" ? chaos : null}
          ch={makeCharacter({ mentor_id: mentorId })}
          tr={(n) => n}
          onPatch={vi.fn()}
        />
      </BooksProvider>
    );

    const { unmount } = render(picker(""));
    const options = () =>
      [...(screen.getByRole("combobox", { name: "導師精霊" }) as HTMLSelectElement).options]
        .map((o) => o.textContent)
        .slice(1);
    expect(options()).toEqual(["Bear"]);
    unmount();

    // A character who already has Chaos can still see — and so drop — it. A
    // <select> that quietly loses its own value reads as "no mentor".
    render(picker("chaos"));
    expect(options()).toEqual(["Bear", "Chaos"]);
  });

  it("gives the page in place of the rulebook's advantage and disadvantage", () => {
    const dog: MentorInfo = {
      ...chaos,
      id: "DOG-1",
      name: "Dog",
      source: "SR5",
      page: "321",
      choices: [],
    };
    render(
      <MentorPicker
        catalog={makeCatalog({
          mentors: [{ id: "DOG-1", name: "Dog", source: "SR5", page: "321" }],
        })}
        mentor={dog}
        ch={makeCharacter({ mentor_id: "DOG-1" })}
        tr={(n) => n}
        onPatch={vi.fn()}
      />,
    );
    expect(screen.getByText("Dog / SR5 p.321（英語版の頁）")).toBeTruthy();
    expect(screen.getByText("利点：効果は計算に反映済み")).toBeTruthy();
    expect(
      screen.getByText(
        "欠点：特定の状況で適用する。内容はルールブックを参照：SR5 p.321（英語版の頁）",
      ),
    ).toBeTruthy();
  });

  it("lists the advantage's fixed effects as the engine applies them", () => {
    const dog: MentorInfo = {
      ...chaos,
      id: "DOG-1",
      name: "Dog",
      source: "SR5",
      page: "321",
      effects: [
        { key: "engine.mentorEffect.skill", params: { names: [{ tr: "Tracking" }], value: "+2" } },
        { key: "engine.mentorEffect.damageResistance", params: { value: "+2" } },
      ],
      choices: [],
    };
    render(
      <MentorPicker
        catalog={makeCatalog({
          mentors: [{ id: "DOG-1", name: "Dog", source: "SR5", page: "321" }],
        })}
        mentor={dog}
        ch={makeCharacter({ mentor_id: "DOG-1" })}
        tr={(n) => (n === "Tracking" ? "トラッキング" : n)}
        onPatch={vi.fn()}
      />,
    );
    expect(
      screen.getByText("利点（計算に反映済み）：トラッキング +2 / ダメージ抵抗 +2"),
    ).toBeTruthy();
  });

  it("puts a granted negative quality with the disadvantage", () => {
    const eagle: MentorInfo = {
      ...chaos,
      id: "EAGLE-1",
      name: "Eagle",
      source: "SR5",
      page: "322",
      effects: [
        {
          key: "engine.mentorEffect.skill",
          params: { names: [{ tr: "Perception" }], value: "+2" },
        },
      ],
      drawbacks: [
        {
          key: "engine.mentorEffect.qualityPick",
          params: { name: { tr: "Allergy (Common, Mild)" }, pick: { tr: "Pollutants" } },
        },
      ],
      choices: [],
    };
    render(
      <MentorPicker
        catalog={makeCatalog({
          mentors: [{ id: "EAGLE-1", name: "Eagle", source: "SR5", page: "322" }],
        })}
        mentor={eagle}
        ch={makeCharacter({ mentor_id: "EAGLE-1" })}
        tr={(n) => n}
        onPatch={vi.fn()}
      />,
    );
    expect(screen.getByText("利点（計算に反映済み）：Perception +2")).toBeTruthy();
    expect(
      screen.getByText(
        "欠点（計算に反映済み）：資質 Allergy (Common, Mild)（Pollutants）。特定の状況で適用するものがあれば、ルールブックを参照：SR5 p.322（英語版の頁）",
      ),
    ).toBeTruthy();
  });

  it("names a choice through the translation table", () => {
    // the core rulebook pass translates these labels; untranslated, they stay English
    renderPicker(vi.fn(), (n) => (n === CHOICE ? "アデプト：向上能力 2 レベル無料" : n));
    expect(screen.getByText("アデプト：向上能力 2 レベル無料")).toBeTruthy();
    expect(screen.queryByText(CHOICE)).toBeNull();
  });

  it("offers a granted power its own target beside the choice's pick", () => {
    // The choice's own select is spent on *which* Improved Potential it grants,
    // so the `<selectlimit>` on the second one needs a select of its own.
    renderPicker();
    const target = screen.getByRole("combobox", {
      name: /Improved Potential \(Chaos Mentor\)/,
    }) as HTMLSelectElement;
    expect([...target.options].map((o) => o.textContent)).toEqual([
      "対象を選択",
      "身体",
      "精神",
      "社交",
    ]);
  });

  it("picks out of the paragon list, and says so, in paragon mode", () => {
    // A paragon shares `mentor_id` — no character can have both — so the only
    // thing that changes is which list is offered and what it is called.
    const onPatch = vi.fn();
    render(
      <MentorPicker
        catalog={makeCatalog({
          mentors: [{ id: "chaos", name: "Chaos", source: "SG", page: "200" }],
          paragons: [{ id: "delphi", name: "Delphi", source: "KC", page: "103" }],
        })}
        mentor={null}
        ch={makeCharacter({})}
        tr={(n) => n}
        onPatch={onPatch}
        paragon
      />,
    );
    const select = screen.getByRole("combobox", { name: "パラゴン" }) as HTMLSelectElement;
    expect([...select.options].map((o) => o.textContent)).toEqual(["選択してください", "Delphi"]);

    fireEvent.change(select, { target: { value: "delphi" } });
    expect(onPatch).toHaveBeenCalledWith({
      mentor_id: "delphi",
      mentor_choices: [],
      mentor_extras: {},
    });
  });

  it("patches the power target under its own key, keeping the choice's", () => {
    const onPatch = renderPicker();
    fireEvent.change(
      screen.getByRole("combobox", { name: /Improved Potential \(Chaos Mentor\)/ }),
      { target: { value: "Social" } },
    );
    expect(onPatch).toHaveBeenCalledWith({ mentor_extras: { [TARGET_KEY]: "Social" } });
  });
});
