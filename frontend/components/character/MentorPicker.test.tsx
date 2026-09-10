import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MentorPicker } from "./MentorPicker";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import type { MentorInfo } from "@/lib/types";

const CHOICE = "Adept: 2 free levels of Improved Potential";
const TARGET_KEY = `${CHOICE} / Improved Potential (Chaos Mentor)`;

const chaos: MentorInfo = {
  id: "chaos",
  name: "Chaos",
  advantage: "",
  disadvantage: "",
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

function renderPicker(onPatch = vi.fn()) {
  const ch = makeCharacter({ mentor_id: "chaos", mentor_choices: [CHOICE] });
  render(
    <MentorPicker
      catalog={makeCatalog({
        mentors: [{ id: "chaos", name: "Chaos", source: "SG", page: "200", advantage: "" }],
      })}
      mentor={chaos}
      ch={ch}
      tr={(n) => n}
      onPatch={onPatch}
    />,
  );
  return onPatch;
}

describe("MentorPicker", () => {
  it("offers a granted power its own target beside the choice's pick", () => {
    // The choice's own select is spent on *which* Improved Potential it grants,
    // so the `<selectlimit>` on the second one needs a select of its own.
    renderPicker();
    const target = screen.getByRole("combobox", {
      name: /Improved Potential \(Chaos Mentor\)/,
    }) as HTMLSelectElement;
    expect([...target.options].map((o) => o.textContent)).toEqual([
      "対象を選択",
      "物理",
      "精神",
      "社会",
    ]);
  });

  it("picks out of the paragon list, and says so, in paragon mode", () => {
    // A paragon shares `mentor_id` — no character can have both — so the only
    // thing that changes is which list is offered and what it is called.
    const onPatch = vi.fn();
    render(
      <MentorPicker
        catalog={makeCatalog({
          mentors: [{ id: "chaos", name: "Chaos", source: "SG", page: "200", advantage: "" }],
          paragons: [{ id: "delphi", name: "Delphi", source: "KC", page: "103", advantage: "" }],
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
