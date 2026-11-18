import { fireEvent, render, screen } from "@testing-library/react";
import { HelpTip } from "@/components/help/HelpTip";
import { initiativeHelp, limitHelp, weaponHelpLines } from "@/lib/character/help-breakdown";
import { translate } from "@/lib/i18n";
import { makeCharacter } from "@/tests/fixtures";

const ui = (key: Parameters<typeof translate>[1], vars?: Record<string, string | number>) =>
  translate("ja", key, vars);

import { bindRuns, fitBox, widthCap } from "./HelpTip";

describe("bindRuns", () => {
  it("keeps a rulebook citation on one line", () => {
    expect(bindRuns("上限（SR5 p.47）")).toBe("上限（SR5\u00a0p.47）");
  });

  it("keeps an operator with the operands on either side of it", () => {
    expect(bindRuns("身体リミット = (STR×2 + BOD + REA) ÷ 3（切り上げ）")).toBe(
      "身体リミット = (STR×2\u00a0+\u00a0BOD\u00a0+\u00a0REA)\u00a0÷\u00a03（切り上げ）",
    );
  });

  it("keeps an operator with the one operand it has", () => {
    expect(bindRuns("関連能力値（+ 修正）")).toBe("関連能力値（+\u00a0修正）");
  });

  it("leaves the spaces that are fine to break at", () => {
    // a space before a number in Japanese prose is an ordinary break
    expect(bindRuns("埋まったマス 3 つごとに")).toBe("埋まったマス 3 つごとに");
    // and so is the one around "=", which is where the formula now wraps
    expect(bindRuns("イニシアティブ = REA")).toBe("イニシアティブ = REA");
  });
});

describe("<HelpTip>", () => {
  const renderTip = () => {
    render(
      <>
        <HelpTip
          label="身体リミット の説明"
          lines={[{ label: "式" }, { label: "合計", value: 5, strong: true }]}
        >
          身体リミット
        </HelpTip>
        <button type="button">外</button>
      </>,
    );
    const button = screen.getByRole("button", { name: "身体リミット の説明" });
    const tip = screen.getByRole("tooltip", { hidden: true });
    const shown = () => tip.parentElement!.hasAttribute("data-open");
    return { button, tip, shown };
  };

  it("describes the button with its lines", () => {
    const { button, tip } = renderTip();
    expect(button.getAttribute("aria-describedby")).toBe(tip.id);
    expect(tip.textContent).toContain("合計5");
  });

  // `data-open` is the only thing the CSS shows the box on, so it is the box
  it("closes on Escape while the button keeps focus", () => {
    const { button, shown } = renderTip();
    fireEvent.focus(button);
    expect(shown()).toBe(true);
    expect(button.getAttribute("aria-expanded")).toBe("true");
    fireEvent.keyDown(button, { key: "Escape" });
    expect(shown()).toBe(false);
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });

  it("closes on Escape while only hovered", () => {
    const { button, shown } = renderTip();
    fireEvent.mouseEnter(button.parentElement!);
    expect(shown()).toBe(true);
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(shown()).toBe(false);
  });

  it("opens on hover and closes when the pointer leaves", () => {
    const { button, shown } = renderTip();
    fireEvent.mouseEnter(button.parentElement!);
    expect(shown()).toBe(true);
    fireEvent.mouseLeave(button.parentElement!);
    expect(shown()).toBe(false);
  });

  // the skills tab settles under a parked pointer: a mouseleave from that
  // must not close a box the keyboard opened
  it("stays open on focus when the pointer leaves", () => {
    const { button, shown } = renderTip();
    fireEvent.mouseEnter(button.parentElement!);
    fireEvent.focus(button);
    fireEvent.mouseLeave(button.parentElement!);
    expect(shown()).toBe(true);
  });

  it("opens again when the pointer comes back after Escape", () => {
    const { button, shown } = renderTip();
    fireEvent.mouseEnter(button.parentElement!);
    fireEvent.keyDown(document.body, { key: "Escape" });
    fireEvent.mouseLeave(button.parentElement!);
    fireEvent.mouseEnter(button.parentElement!);
    expect(shown()).toBe(true);
  });

  it("stays open after a tap until a second tap, even while hovered and focused", () => {
    const { button, shown } = renderTip();
    // the order a desktop click arrives in: hover, focus, click
    fireEvent.mouseEnter(button.parentElement!);
    fireEvent.focus(button);
    fireEvent.click(button);
    fireEvent.mouseLeave(button.parentElement!);
    expect(shown()).toBe(true);
    fireEvent.mouseEnter(button.parentElement!);
    fireEvent.click(button);
    expect(shown()).toBe(false);
  });

  it("closes on a tap outside it", () => {
    const { button, shown } = renderTip();
    fireEvent.click(button);
    expect(shown()).toBe(true);
    fireEvent.pointerDown(screen.getByRole("button", { name: "外" }));
    expect(shown()).toBe(false);
  });

  it("closes when the focus leaves it", () => {
    const { button, shown } = renderTip();
    fireEvent.click(button);
    fireEvent.focusOut(button, { relatedTarget: screen.getByRole("button", { name: "外" }) });
    expect(shown()).toBe(false);
  });
});

describe("fitBox", () => {
  const window = { left: 0, top: 0, right: 400, bottom: 800 };
  const at = (left: number, top: number) => ({ left, top, right: left + 80, bottom: top + 20 });

  it("hangs off the label's left edge when there is room", () => {
    expect(fitBox(at(20, 100), window, 200, 100)).toEqual({ left: 0, above: false });
  });

  it("slides left to stay inside the right edge", () => {
    // 400 - 8 - 200 = 192, the box's left edge on screen
    expect(fitBox(at(300, 100), window, 200, 100).left).toBe(192 - 300);
  });

  it("goes above when it would run past the bottom and there is more room above", () => {
    expect(fitBox(at(20, 740), window, 200, 100).above).toBe(true);
  });

  it("stays below when neither side fits but below has more room", () => {
    expect(fitBox(at(20, 100), { ...window, bottom: 400 }, 200, 500).above).toBe(false);
  });

  it("caps the width to the panel it is in", () => {
    expect(widthCap({ left: 0, top: 0, right: 304, bottom: 800 })).toBe(288);
    expect(widthCap(window)).toBe(352);
    expect(widthCap({ left: 0, top: 0, right: 100, bottom: 800 })).toBe(120);
  });
});

describe("limitHelp", () => {
  it("splits each limit into its formula base and the modifiers on top", () => {
    const d = makeCharacter().derived;
    d.totals = { BOD: 4, AGI: 3, REA: 3, STR: 2, LOG: 3, INT: 3, WIL: 3, CHA: 3 };
    d.essence = 5.1;
    d.limits = { physical: 4, mental: 4, social: 6 };
    const lines = limitHelp(d, ui);
    // physical: ceil((2*STR + BOD + REA)/3) = ceil(11/3) = 4
    expect(lines.slice(0, 3).map((l) => l.value)).toEqual([undefined, 4, 4]);
    // mental: ceil(12/3) = 4
    expect(lines[4].value).toBe(4);
    // Social limit rounds Essence up before calculating: ceil((6+3+6)/3) = 5, +1 elsewhere
    const social = lines.slice(6);
    expect(social.map((l) => l.value)).toEqual([undefined, 5, "+1", 6, undefined]);
    expect(social[0].label).toContain("ESSは先に切り上げ");
  });
});

describe("named sources", () => {
  it("lists each source and puts what they do not explain on one other line", () => {
    const d = makeCharacter().derived;
    d.totals = { REA: 3, INT: 3 };
    d.initiative = { value: 8, dice: 3 };
    d.stat_sources = {
      initiative: [{ source: "Wired Reflexes", value: 2 }],
      // two non-stacking dice bonuses: 2 + 1 listed, only 2 counted
      initiative_dice: [
        { source: "Wired Reflexes", value: 2 },
        { source: "Jazz", value: 1 },
      ],
    };
    const lines = initiativeHelp(d, ui, (n) => `訳:${n}`);
    expect(lines.slice(0, 4).map((l) => [l.label, l.value])).toEqual([
      ["イニシアティブ = REA + INT", undefined],
      ["基本値", 6],
      ["訳:Wired Reflexes", "+2"],
      ["合計", 8],
    ]);
    const dice = lines.slice(4);
    expect(dice.map((l) => l.value)).toEqual([undefined, 1, "+2", "+1", -1, 3, undefined]);
    expect(dice[4].label).toBe("その他（重複しない分など）");
  });
});

describe("weaponHelpLines", () => {
  it("explains only the stats the weapon actually has", () => {
    const knife = weaponHelpLines(
      { accuracy: "5", damage: "(STR/2+2)P", ap: "-1", reach: "1" },
      ui,
    );
    expect(knife.map((l) => l.label)).toEqual([
      ui("help.weapon.acc"),
      ui("help.weapon.dv"),
      ui("help.weapon.ap"),
      ui("help.weapon.reach"),
    ]);
    // "-" and "0" are how the catalog writes "this stat does not apply"
    const pistol = weaponHelpLines(
      { accuracy: "6", damage: "8P", ap: "-", rc: "0", mode: "SA", ammo: "15(c)", reach: "0" },
      ui,
    );
    expect(pistol.map((l) => l.label)).toEqual([
      ui("help.weapon.acc"),
      ui("help.weapon.dv"),
      ui("help.weapon.mode"),
      ui("help.weapon.ammo"),
    ]);
  });
});
