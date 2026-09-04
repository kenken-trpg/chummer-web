import { render, screen } from "@testing-library/react";
import { CharacterSidebar } from "@/components/character/CharacterSidebar";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import { LOCALE_STORAGE_KEY } from "@/lib/i18n";

/* eslint-disable @typescript-eslint/no-explicit-any */

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
        tradition: { name: "Hermeticism" } as any,
        errors: ["something wrong"],
      },
    });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("両利き")).toBeDefined();
    expect(screen.getByText("伝統")).toBeDefined();
    expect(screen.getByText("something wrong")).toBeDefined();
  });

  it("SidebarEconomy always shows the ニューエン row", () => {
    const ch = makeCharacter({ derived: { nuyen: 12500 } });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("ニューエン").nextSibling?.textContent).toBe("12,500¥");
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
      derived: { enabled_tabs: ["initiation"], initiation: { grade: 2, karma: 13 } as any },
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
      expect(screen.queryByText("イニシアチブ")).toBeNull();
    } finally {
      window.localStorage.removeItem(LOCALE_STORAGE_KEY);
    }
  });

  it("keeps engine-authored errors and warnings verbatim", () => {
    // These sentences come from the Python engine. The sidebar must not try to
    // localise them — that needs the backend translated too (docs/i18n.md).
    const ch = makeCharacter({
      derived: { errors: ["カルマが足りません"], warnings: ["未使用ニューエン"] },
    });
    render(
      <CharacterSidebar catalog={makeCatalog()} character={ch} d={ch.derived} tr={identityTr} />,
    );
    expect(screen.getByText("カルマが足りません")).toBeDefined();
    expect(screen.getByText("未使用ニューエン")).toBeDefined();
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
    expect(screen.getByRole("spinbutton", { name: "SC 編集" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "悪名ボーナス" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "カルマ" })).toBeDefined();
    expect(screen.getByRole("spinbutton", { name: "ニューエン" })).toBeDefined();
  });
});
