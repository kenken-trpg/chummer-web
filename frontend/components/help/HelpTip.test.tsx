import { fireEvent, render, screen } from "@testing-library/react";
import { HelpTip } from "@/components/help/HelpTip";
import { limitHelp } from "@/lib/character/help-breakdown";
import { translate } from "@/lib/i18n";
import { makeCharacter } from "@/tests/fixtures";

const ui = (key: Parameters<typeof translate>[1], vars?: Record<string, string | number>) =>
  translate("ja", key, vars);

describe("<HelpTip>", () => {
  it("describes the button with its lines and toggles on tap", () => {
    render(
      <HelpTip
        label="物理リミット の説明"
        lines={[{ label: "式" }, { label: "合計", value: 5, strong: true }]}
      >
        物理リミット
      </HelpTip>,
    );
    const button = screen.getByRole("button", { name: "物理リミット の説明" });
    const tip = screen.getByRole("tooltip", { hidden: true });
    expect(button.getAttribute("aria-describedby")).toBe(tip.id);
    expect(tip.textContent).toContain("合計5");
    fireEvent.click(button);
    expect(button.getAttribute("aria-expanded")).toBe("true");
    fireEvent.keyDown(button, { key: "Escape" });
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });
});

describe("limitHelp", () => {
  it("splits each limit into its formula base and the modifiers on top", () => {
    const d = makeCharacter().derived;
    d.totals = { BOD: 4, AGI: 3, REA: 3, STR: 2, LOG: 3, INT: 3, WIL: 3, CHA: 3 };
    d.essence = 6;
    d.limits = { physical: 6, mental: 4, social: 6 };
    const lines = limitHelp(d, ui);
    // physical: ceil((8+3+3+2)/3) = 6, no modifier line
    expect(lines.slice(0, 3).map((l) => l.value)).toEqual([undefined, 6, 6]);
    // mental: ceil(12/3) = 4
    expect(lines[4].value).toBe(4);
    // social: ceil((6+3+6)/3) = 5, +1 from somewhere
    const social = lines.slice(6);
    expect(social.map((l) => l.value)).toEqual([undefined, 5, "+1", 6, undefined]);
  });
});
