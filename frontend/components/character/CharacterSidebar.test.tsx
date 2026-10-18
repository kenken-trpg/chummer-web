import { fireEvent, render, screen } from "@testing-library/react";
import { CharacterSidebar } from "@/components/character/CharacterSidebar";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import { LOCALE_STORAGE_KEY } from "@/lib/i18n";

describe("<CharacterSidebar>", () => {
  it("renders name, the 能力値 block and 作成 mode for a fresh character", () => {
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={makeCharacter({ name: "Vex" })}
        d={makeCharacter().derived}
        tr={identityTr}
      />,
    );
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe("Vex");
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("能力値");
    expect(screen.getByText("モード").nextSibling?.textContent).toBe("作成");
    expect(screen.getByText("作成ルール上は問題なし")).toBeDefined();
  });

  it("explains the availability limit behind a help button", () => {
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={makeCharacter()}
        d={makeCharacter().derived}
        tr={identityTr}
      />,
    );
    const button = screen.getByRole("button", { name: "入手値上限 の説明" });
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("Forbidden");
  });

  it("explains what Essence is and what it takes with it", () => {
    const ch = makeCharacter();
    ch.derived!.enabled_tabs = ["MAG"];
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    const button = screen.queryByRole("button", { name: "エッセンス の説明" });
    expect(button).not.toBeNull();
    const tip = document.getElementById(button!.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("誰でも 6 から始まり");
  });

  it("explains spell resistance, and a defence line's formula and total dice", () => {
    const ch = makeCharacter({
      derived: {
        spell_resistance: 1,
        spell_defense: {
          general: 1,
          direct_mana: 1,
          detection: 3,
          mental_manipulation: 1,
          mana_illusion: 1,
          physical_illusion: 1,
          decrease: {},
        },
        spell_defense_pools: { detection: 9 } as never,
      },
    });
    ch.derived!.enabled_tabs = ["MAG"];
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    const tipOf = (name: string) => {
      const button = screen.getByRole("button", { name: `${name} の説明` });
      // HelpTip binds a formula's runs with no-break spaces
      return document
        .getElementById(button.getAttribute("aria-describedby")!)
        ?.textContent?.replace(/\u00a0/g, " ");
    };
    expect(tipOf("呪文抵抗")).toContain("間接呪文の回避は除く");
    const detection = tipOf("探知");
    expect(detection).toContain("LOG + WIL + 修正");
    expect(detection).toContain("+3");
    expect(detection).toContain("9");
    // a line equal to the general resistance is not shown, so it has no tip
    expect(screen.queryByRole("button", { name: "直接マナ の説明" })).toBeNull();
  });

  it("explains the damage resistance bonus with the pool it goes into", () => {
    const ch = makeCharacter({
      derived: {
        damage_resistance: 2,
        damage_resist: { pool: 13, body: 5, armor: 6, bonus: 2 },
      },
    });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    const button = screen.getByRole("button", { name: "ダメージ抵抗 の説明" });
    const tip = document
      .getElementById(button.getAttribute("aria-describedby")!)
      ?.textContent?.replace(/\u00a0/g, " ");
    expect(tip).toContain("BOD + 装甲 + 修正");
    expect(tip).toContain("強靱力");
    expect(tip).toContain("13");
  });

  it("explains a test modifier with its attributes, and totals it only when they are the rest", () => {
    const ch = makeCharacter({
      derived: {
        totals: { LOG: 4, WIL: 3, BOD: 5, CHA: 2, INT: 3 },
        fatigue_resist: 2,
        test_mods: { memory: 2, judge_intentions: 1 },
        unarmed_dv: 1,
        action_dice_pools: [
          { category: "Matrix", name: "Hack on the Fly", bonus: 2, source: "Codeslinger" },
        ],
      } as never,
    });
    ch.derived!.enabled_tabs = ["MAG"];
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    const tipOf = (name: string) => {
      const button = screen.getByRole("button", { name: `${name} の説明` });
      return document
        .getElementById(button.getAttribute("aria-describedby")!)
        ?.textContent?.replace(/\u00a0/g, " ");
    };
    // LOG 4 + WIL 3 + 2
    expect(tipOf("記憶")).toContain("LOG + WIL + 修正");
    expect(tipOf("記憶")).toMatch(/合計9$/);
    // BOD 5 + WIL 3 + 2
    expect(tipOf("疲労抵抗")).toMatch(/合計10$/);
    // Chummer's Judge Intentions takes another modifier too, so no total here
    expect(tipOf("意図看破")).toContain("CHA + INT + 修正");
    expect(tipOf("意図看破")).not.toContain("合計");
    expect(tipOf("非武装DV")).toContain("素手");
    expect(tipOf("Matrix: Hack on the Fly")).toContain("Codeslinger");
  });

  it("switches to キャリア mode and shows the reward panel when career + patch", () => {
    const ch = makeCharacter({ career: true });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        patch={() => {}}
      />,
    );
    expect(screen.getByText("モード").nextSibling?.textContent).toBe("キャリア");
    expect(screen.getByText("報酬合計")).toBeDefined();
    expect(screen.getByRole("button", { name: "報酬を追加" })).toBeDefined();
  });

  it("surfaces flag + awakened rows when the derived data is present", () => {
    const ch = makeCharacter({
      derived: {
        ambidextrous: true,
        tradition: { name: "Hermeticism" } as never,
        errors: [{ key: "engine.attrs.essenceDepleted" }],
      },
    });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("両利き")).toBeDefined();
    expect(screen.getByText("様式")).toBeDefined();
    expect(screen.getByText("エッセンスが0以下です")).toBeDefined();
  });

  it("SidebarEconomy always shows the 新円 row", () => {
    const ch = makeCharacter({ derived: { nuyen: 12500 } });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("新円").nextSibling?.textContent).toBe("12,500¥");
  });

  it("SidebarAwakened shows イニシエーション only when the tab is enabled", () => {
    const plain = makeCharacter();
    const { unmount } = render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={plain}
        d={plain.derived}
        tr={identityTr}
      />,
    );
    expect(screen.queryByText("イニシエーション")).toBeNull();
    unmount();

    const initiate = makeCharacter({
      derived: { enabled_tabs: ["initiation"], initiation: { grade: 2, karma: 13 } as never },
    });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={initiate}
        d={initiate.derived}
        tr={identityTr}
      />,
    );
    expect(screen.getByText("イニシエーション")).toBeDefined();
  });

  // The point of moving the sidebar's copy into `lib/i18n`: it is on screen at
  // all times, so if it stays Japanese under `en` the locale switch is
  // decorative. This fails the moment a literal creeps back into a block.
  it("renders in English when the locale is en", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    try {
      const ch = makeCharacter({ name: "Vex" });
      render(
        <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
      );
      expect(screen.getByText("Mode")).toBeDefined();
      expect(screen.getByText("Initiative")).toBeDefined();
      expect(screen.getByRole("heading", { name: "Attributes" })).toBeDefined();
      expect(screen.getByText("No chargen rule problems")).toBeDefined();
      expect(screen.queryByText("イニシアティブ")).toBeNull();
    } finally {
      window.localStorage.removeItem(LOCALE_STORAGE_KEY);
    }
  });

  it("renders engine notices in the current locale", () => {
    // The engine ships `{key, params}`; the sidebar looks the wording up like
    // any other app copy (docs/i18n.md).
    const ch = makeCharacter({
      derived: {
        errors: [{ key: "engine.karma.negative", params: { karma: -3 } }],
        warnings: [{ key: "engine.contacts.unnamed" }],
      },
    });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("カルマが不足しています（残り -3）")).toBeDefined();
    expect(screen.getByText("名前のないコンタクトがあります")).toBeDefined();
  });

  it("names the career-panel number fields", () => {
    const ch = makeCharacter({ career: true });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        patch={() => {}}
      />,
    );
    // bare number boxes, previously announced as "spin button" with no name
    expect(screen.getByRole("spinbutton", { name: "SC 補正" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "悪名ボーナス" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "カルマ" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "新円" })).toBeDefined();
  });

  it("shows where the street cred comes from", () => {
    const ch = makeCharacter({
      career: true,
      street_cred: 3,
      derived: {
        karma_earned: 45,
        street_cred: 5,
        street_cred_earned: 2,
        street_cred_divisor: 20,
      } as never,
    });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        patch={() => {}}
      />,
    );
    expect(screen.getByText("SC = 得たカルマ 45 ÷ 20 → 2 ＋ 補正 3 ＝ 5")).toBeDefined();
  });

  it("burns street cred two at a time and can take a burn back", () => {
    const patch = vi.fn();
    const ch = makeCharacter({
      career: true,
      burnt_street_cred: 2,
      derived: { street_cred: 3 } as never,
    });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        patch={patch}
      />,
    );
    expect(screen.getByText("燃やした SC 2")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "SC を 2 燃やす（悪名 −1）" }));
    expect(patch).toHaveBeenCalledWith({ burnt_street_cred: 4 });
    fireEvent.click(screen.getByRole("button", { name: "燃やしを戻す" }));
    expect(patch).toHaveBeenCalledWith({ burnt_street_cred: 0 });
  });

  it("will not burn below two points", () => {
    const ch = makeCharacter({ career: true, derived: { street_cred: 1 } as never });
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        patch={() => {}}
      />,
    );
    const burn = screen.getByRole("button", {
      name: "SC を 2 燃やす（悪名 −1）",
    }) as HTMLButtonElement;
    expect(burn.disabled).toBe(true);
  });

  it("puts an action's failure in a live region", () => {
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={makeCharacter()}
        d={makeCharacter().derived}
        tr={identityTr}
        error="保存できませんでした"
      />,
    );
    expect(screen.getByRole("alert").textContent).toBe("保存できませんでした");
  });

  it("keeps the region on screen while there is nothing to say", () => {
    // A role added along with the text is announced only patchily; the region
    // has to be there first, which means it is there when empty too.
    render(
      <CharacterSidebar
        catalog={makeCatalog()}
        character={makeCharacter()}
        d={makeCharacter().derived}
        tr={identityTr}
      />,
    );
    expect(screen.getByRole("alert").textContent).toBe("");
  });
});
