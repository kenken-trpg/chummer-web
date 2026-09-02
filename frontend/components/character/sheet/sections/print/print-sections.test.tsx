import { render } from "@testing-library/react";
import { buildSheetData } from "@/lib/character/sheet-data";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import { PrintStatBlock } from "./PrintStatBlock";
import { PrintConditionMonitor } from "./PrintConditionMonitor";

/* eslint-disable @typescript-eslint/no-explicit-any */

const s = buildSheetData({
  character: makeCharacter({
    derived: {
      totals: { BOD: 5, AGI: 3, REA: 4, STR: 3, CHA: 3, INT: 4, LOG: 3, WIL: 4, EDG: 4, MAG: 5 },
      armor: 9,
      damage_resistance: 2,
      essence: 5.4,
      enabled_tabs: ["MAG"],
      cm_recovery: { physical: 2, stun: 3 },
      limit_modifiers: [{ limit: "physical", value: 1, condition: "全力疾走" }],
      lifestyle: { id: "l1", name: "Low", months: 2, increment: "month" } as any,
    },
  }),
  catalog: makeCatalog(),
  tr: identityTr,
  layout: "print",
});

describe("print sections", () => {
  it("PrintStatBlock renders the attribute row and derived pools", () => {
    const { container } = render(<PrintStatBlock {...(s as any)} />);
    expect(container.querySelector("section.print-statblock")).not.toBeNull();
    // one attr cell per enabled attribute (MAG on, RES off)
    expect(container.querySelectorAll(".print-attr")).toHaveLength(10);
    const text = container.textContent || "";
    expect(text).toContain("防御プール"); // REA+INT = 8
    expect(text).toContain("8");
    expect(text).toContain("ダメージ抵抗"); // BOD+armor+resist = 16
    expect(text).toContain("16");
    expect(text).toContain("エッセンス");
    expect(text).toContain("5.40");
    expect(text).toContain("条件リミット (physical)");
    expect(text).toContain("ライフスタイル: Low 2");
  });

  it("PrintConditionMonitor draws one box per CM point plus BOD/2 overflow", () => {
    const { container } = render(<PrintConditionMonitor {...(s as any)} />);
    // physical 10 + overflow ceil(5/2)=3 + stun 10
    expect(container.querySelectorAll(".cm-box")).toHaveLength(23);
    expect(container.querySelectorAll(".print-cm-boxes--overflow .cm-box")).toHaveLength(3);
    // −1 marker every third box: 10/3 -> 3 per track
    expect(
      container.querySelectorAll(".print-cm-boxes:not(.print-cm-boxes--overflow) .cm-box--mark"),
    ).toHaveLength(6);
    expect(container.textContent).toContain("回復 2/日");
    expect(container.textContent).toContain("回復 3/時間");
  });
});
