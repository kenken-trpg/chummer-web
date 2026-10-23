import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { AttrsTab } from "@/components/character/tabs/AttrsTab";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    patch?: (b: Record<string, unknown>) => void;
    setCharacter?: (c: Character) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <AttrsTab
      catalog={makeCatalog()}
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

describe("<AttrsTab>", () => {
  it("renders the 9 physical/mental sliders and the point line, hiding MAG/RES", () => {
    renderTab();
    expect(screen.getAllByRole("slider")).toHaveLength(9);
    expect(screen.getByText(/能力値点 0\/0 ・ 特殊点 0\/0/)).toBeDefined();
  });

  it("explains each attribute behind a help button", () => {
    renderTab();
    const button = screen.getAllByRole("button", { name: /の説明$/ })[0];
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("強靱力。ダメージ抵抗");
  });

  const split = {
    levels: { AGI: 1 },
    floors: { BOD: 1, AGI: 1, REA: 1, STR: 1, CHA: 1, INT: 1, LOG: 1, WIL: 1, EDG: 1 },
    karma: 20,
  };

  it("lets a Priority creation mark attribute levels as bought with karma", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        attributes: { AGI: 4, BOD: 3 },
        attribute_karma: { AGI: 1 },
        derived: { attribute_karma: split } as never,
      },
    });
    const agi = screen.getByRole("spinbutton", { name: /AGI.*うちカルマ/ }) as HTMLInputElement;
    expect(agi.value).toBe("1");
    expect(agi.max).toBe("3"); // AGI 4 over a floor of 1
    expect(screen.getByText("カルマで上げた能力値：20 カルマ")).toBeDefined();
    fireEvent.change(screen.getByRole("spinbutton", { name: /BOD.*うちカルマ/ }), {
      target: { value: "2" },
    });
    expect(patch).toHaveBeenCalledWith({ attribute_karma: { AGI: 1, BOD: 2 } });
  });

  it("offers no split in a Karma build or after creation", () => {
    for (const character of [
      { derived: { attribute_karma: split, karma_chargen: { enabled: true } } as never },
      { career: true, derived: { attribute_karma: split } as never },
    ]) {
      const { unmount } = renderTab({ character });
      expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
      unmount();
    }
  });

  it("shows the MAG row once the MAG tab is enabled", () => {
    renderTab({ character: { derived: { enabled_tabs: ["MAG"], totals: { MAG: 4 } as never } } });
    expect(screen.getAllByRole("slider")).toHaveLength(10);
  });

  it("shows an A.I.'s Depth and leaves out the body it does not have", () => {
    renderTab({
      character: {
        metatype: "A.I.",
        talent: "A.I.",
        attributes: { DEP: 3 },
        derived: {
          enabled_tabs: ["DEP", "advanced programs"],
          totals: { DEP: 3 } as never,
          metatype_info: {
            attributes: {
              BOD: { min: 0, max: 0, aug: 0 },
              AGI: { min: 0, max: 0, aug: 0 },
              REA: { min: 0, max: 0, aug: 0 },
              STR: { min: 0, max: 0, aug: 0 },
              DEP: { min: 3, max: 6, aug: 6 },
            },
          } as never,
        },
      },
    });
    const names = screen.getAllByRole("slider").map((el) => el.getAttribute("aria-label"));
    expect(names.some((name) => name?.startsWith("BOD"))).toBe(false);
    const dep = screen.getByRole("slider", { name: /^DEP / }) as HTMLInputElement;
    expect([dep.min, dep.max, dep.value]).toEqual(["3", "6", "3"]);
    // the four mental attributes, EDG and DEP
    expect(names).toHaveLength(6);
  });

  it("hides DEP from everyone else", () => {
    renderTab();
    expect(screen.queryByRole("slider", { name: /^DEP / })).toBeNull();
  });

  it("edits a Mundane centaur's native MAG above its free floor", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        metatype: "Centaur",
        talent: "Mundane",
        attributes: { MAG: 3 },
        derived: {
          enabled_tabs: ["MAG", "critter"],
          totals: { MAG: 3 },
          metatype_info: { attributes: { MAG: { min: 1, max: 6, aug: 6 } } },
          attribute_karma: { ...split, floors: { ...split.floors, MAG: 1 }, levels: {} },
        } as never,
      },
    });
    const slider = screen.getByRole("slider", { name: /^MAG / }) as HTMLInputElement;
    expect([slider.min, slider.max, slider.value]).toEqual(["1", "6", "3"]);
    const karma = screen.getByRole("spinbutton", { name: /MAG.*うちカルマ/ }) as HTMLInputElement;
    expect(karma.max).toBe("2");
    fireEvent.change(karma, { target: { value: "1" } });
    expect(patch).toHaveBeenCalledWith({ attribute_karma: { MAG: 1 } });
  });

  it("shows the range essence loss left beside MAG, keeping the slider on what was bought", () => {
    renderTab({
      character: {
        attributes: { MAG: 3 },
        derived: {
          enabled_tabs: ["MAG"],
          totals: { MAG: 1 },
          metatype_info: {
            attributes: { MAG: { min: 2, max: 6, aug: 6, ess_min: 0, ess_max: 3 } },
          },
        } as never,
      },
    });
    const slider = screen.getByRole("slider", { name: /^MAG / }) as HTMLInputElement;
    expect([slider.min, slider.max, slider.value]).toEqual(["2", "6", "3"]);
    expect(screen.getByText("/3")).toBeDefined();
    expect(screen.getByText(/エッセンスで下限 0・上限 3/)).toBeDefined();
  });

  it("adds nothing when essence loss leaves the range alone", () => {
    renderTab({ character: { derived: { enabled_tabs: ["MAG"], totals: { MAG: 4 } as never } } });
    expect(screen.queryByText(/エッセンスで下限/)).toBeNull();
  });

  it("drags STR: onChange previews via setCharacter, onMouseUp commits via patch", () => {
    const patch = vi.fn();
    // AttrsTab is a controlled slider — the preview only sticks if setCharacter
    // actually re-renders it, so drive it through real state here.
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter());
      return (
        <AttrsTab
          catalog={makeCatalog()}
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
    const str = screen.getAllByRole("slider")[3]; // BOD, AGI, REA, STR
    fireEvent.change(str, { target: { value: "5" } });
    expect((str as HTMLInputElement).value).toBe("5");
    fireEvent.mouseUp(str);
    expect(patch).toHaveBeenCalledWith({ attributes: expect.objectContaining({ STR: 5 }) });
  });

  it("starts an unset attribute at the metatype minimum, not at zero", () => {
    renderTab({
      character: {
        attributes: {},
        derived: {
          metatype_info: {
            name: "Troll",
            attributes: { BOD: { min: 5, max: 10, aug: 14 } },
          },
        } as never,
      },
    });
    const bod = screen.getAllByRole("slider")[0] as HTMLInputElement;
    expect(bod.min).toBe("5");
    expect(bod.value).toBe("5");
  });

  it("raises a stored rating that sits under the metatype floor", () => {
    // a Human BOD 1 kept across a swap to Troll. The engine clamps it up on
    // the next compute; showing 1 until then makes the slider disagree with
    // the number beside it.
    renderTab({
      character: {
        attributes: { BOD: 1 },
        derived: {
          metatype_info: {
            name: "Troll",
            attributes: { BOD: { min: 5, max: 10, aug: 14 } },
          },
        } as never,
      },
    });
    expect((screen.getAllByRole("slider")[0] as HTMLInputElement).value).toBe("5");
  });

  it("marks the racial minimum on the scale", () => {
    const { container } = renderTab({
      character: {
        attributes: { BOD: 7 },
        derived: {
          metatype_info: {
            name: "Troll",
            attributes: { BOD: { min: 5, max: 10, aug: 14 } },
          },
        } as never,
      },
    });
    expect(container.querySelector(".range-tick.floor")?.textContent).toBe("5");
    expect(container.querySelector(".range-tick.here")?.textContent).toBe("7");
  });

  it("says whose ranges these are when a quality replaced the metatype's", () => {
    const { container } = renderTab({
      character: {
        derived: {
          metatype_info: {
            name: "Human",
            attributes: { BOD: { min: 3, max: 10, aug: 14 } },
            attributes_replaced_by: ["Infected: Ghoul (Human)"],
          },
        } as never,
      },
    });
    expect(container.textContent).toContain("Infected: Ghoul (Human)");
  });

  it("shows a shapeshifter's metahuman form beside each attribute it bought in animal form", () => {
    const base = makeCharacter();
    renderTab({
      character: {
        metatype: "Shapeshifter: Vulpine",
        metavariant: "Human",
        derived: {
          metatype_info: {
            ...base.derived.metatype_info,
            parent: "Shapeshifter: Vulpine",
            metahuman_form: {
              name: "Human",
              attributes: {
                AGI: { rating: 3, total: 3, min: 1, max: 6, aug: 10 },
                EDG: { rating: 4, total: 4, min: 2, max: 7, aug: 7 },
              },
              movement: {
                walk: "6",
                run: "12",
                sprint: "2",
                sprint_bonus: 0,
              },
            },
          },
        },
      },
    });
    expect(screen.getByText(/人間形態 3/)).toBeDefined();
    expect(screen.getByText(/人間形態 4/)).toBeDefined();
    expect(screen.getByText(/Shapeshifter: Vulpine の範囲で能力値を振ります/)).toBeDefined();
  });

  it("switches the form the shapeshifter is in, keeping the animal's totals by its sliders", () => {
    const base = makeCharacter();
    const patch = vi.fn();
    const { container } = renderTab({
      patch,
      character: {
        metatype: "Shapeshifter: Vulpine",
        metavariant: "Human",
        derived: {
          // in the metahuman form `totals` is that body's; the animal's is apart
          totals: { ...base.derived.totals, AGI: 3 },
          metatype_info: {
            ...base.derived.metatype_info,
            parent: "Shapeshifter: Vulpine",
            active_form: "metahuman",
            animal_form: { name: "Shapeshifter: Vulpine", totals: { AGI: 4 }, movement: null },
            metahuman_form: {
              name: "Human",
              attributes: { AGI: { rating: 3, total: 3, min: 1, max: 6, aug: 10 } },
              movement: null,
            },
          },
        },
      },
    });
    const select = screen.getByRole("combobox", { name: "今の姿" }) as HTMLSelectElement;
    expect(select.value).toBe("metahuman");
    expect(container.textContent).toContain("4 /");
    fireEvent.change(select, { target: { value: "animal" } });
    expect(patch).toHaveBeenCalledWith({ shapeshifter_form: "animal" });
  });

  it("says nothing of forms for anyone else", () => {
    renderTab();
    expect(screen.queryByText(/人間形態/)).toBeNull();
    expect(screen.queryByRole("combobox", { name: "今の姿" })).toBeNull();
  });
});
