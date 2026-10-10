import { createRef } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { Mock } from "vitest";
import { Toolbar } from "@/components/character/Toolbar";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";
import { LOCALE_STORAGE_KEY } from "@/lib/i18n";

function makeEd(over: Partial<CharacterEditor> = {}): CharacterEditor {
  return {
    roster: [],
    tr: identityTr,
    history: { counts: { undo: 0, redo: 0 } },
    copied: null,
    setCh: vi.fn(),
    patch: vi.fn().mockResolvedValue(undefined),
    undo: vi.fn(),
    redo: vi.fn(),
    openCharacter: vi.fn(),
    newCharacter: vi.fn(),
    deleteCurrent: vi.fn(),
    duplicateCurrent: vi.fn(),
    onImport: vi.fn(),
    download: vi.fn(),
    downloadChum5: vi.fn(),
    downloadXlsx: vi.fn().mockResolvedValue(undefined),
    downloadFvtt: vi.fn().mockResolvedValue(undefined),
    downloadUdonarium: vi.fn(),
    copyText: vi.fn(),
    copyShareLink: vi.fn().mockResolvedValue(undefined),
    refreshRoster: vi.fn(),
    ...over,
  } as unknown as CharacterEditor;
}

describe("<Toolbar>", () => {
  const base = {
    ch: makeCharacter({ name: "Vex" }),
    catalog: makeCatalog(),
    setTab: vi.fn(),
    setSheetLayout: vi.fn(),
    fileRef: createRef<HTMLInputElement>(),
  };

  it("renders the core actions and wires 複製 / JSON保存", () => {
    const ed = makeEd();
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);

    fireEvent.click(screen.getByRole("button", { name: "複製" }));
    expect(ed.duplicateCurrent).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "JSON保存" }));
    expect(ed.download).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "FVTT書出" }));
    expect(ed.downloadFvtt).toHaveBeenCalledTimes(1);
  });

  it("shows シート表示 outside the sheet tab and the layout picker on it", () => {
    const { rerender } = render(
      <Toolbar ed={makeEd()} {...base} tab={"priority"} sheetLayout={"standard"} />,
    );
    expect(screen.getByRole("button", { name: "シート表示" })).toBeDefined();
    expect(screen.queryByRole("button", { name: "印刷 / PDF" })).toBeNull();

    rerender(<Toolbar ed={makeEd()} {...base} tab={"sheet"} sheetLayout={"standard"} />);
    expect(screen.getByRole("button", { name: "印刷 / PDF" })).toBeDefined();
    expect(screen.queryByRole("button", { name: "シート表示" })).toBeNull();
  });

  it("disables undo / redo when the history is empty", () => {
    render(
      <Toolbar
        ed={makeEd({ history: { counts: { undo: 0, redo: 0 } } as CharacterEditor["history"] })}
        {...base}
        tab={"priority"}
        sheetLayout={"standard"}
      />,
    );
    expect(screen.getByRole("button", { name: /元に戻す/ })).toHaveProperty("disabled", true);
    expect(screen.getByRole("button", { name: /やり直し/ })).toHaveProperty("disabled", true);
  });
  // The toolbar's two comboboxes and the name field have no visible <label>;
  // without an accessible name a screen reader announces them as bare
  // "combobox" / "edit text". Assert by role+name so a dropped aria-label
  // fails here rather than silently.
  it("gives every unlabelled control an accessible name", () => {
    render(<Toolbar ed={makeEd()} {...base} tab={"sheet"} sheetLayout={"standard"} />);
    expect(screen.getByRole("combobox", { name: "保存済みキャラクター" })).toBeDefined();
    expect(screen.getByRole("combobox", { name: "レイアウト" })).toBeDefined();
    expect(screen.getByRole("textbox", { name: "キャラクター名" })).toHaveProperty("value", "Vex");
  });

  // The reason the extraction is worth doing at all: with the copy in the
  // components, switching to `en` left the toolbar in Japanese. This is the
  // regression test for that — it fails the moment a literal creeps back in.
  it("renders in English when the locale is en", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    try {
      render(<Toolbar ed={makeEd()} {...base} tab={"sheet"} sheetLayout={"standard"} />);
      expect(screen.getByRole("button", { name: "Duplicate" })).toBeDefined();
      expect(screen.getByRole("button", { name: "Save JSON" })).toBeDefined();
      expect(screen.getByRole("combobox", { name: "Saved characters" })).toBeDefined();
      expect(screen.getByRole("textbox", { name: "Character name" })).toBeDefined();
      expect(screen.queryByText("複製")).toBeNull();
    } finally {
      window.localStorage.removeItem(LOCALE_STORAGE_KEY);
    }
  });
  // Everything above renders the toolbar; these press the buttons. The copy
  // builders in `lib/cocofolia` have tests of their own — what was untested is
  // the wiring, which is where a swapped argument or a wrong `copied` key
  // would sit while the builders stayed green.
  it("hands the roster picker's choice to openCharacter, and __new__ to newCharacter", () => {
    const ed = makeEd({
      roster: [{ id: "other", name: "Kira", metatype: "Elf", career: true }],
    } as Partial<CharacterEditor>);
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);
    const picker = screen.getByRole("combobox", { name: "保存済みキャラクター" });

    fireEvent.change(picker, { target: { value: "other" } });
    expect(ed.openCharacter).toHaveBeenCalledWith("other");

    fireEvent.change(picker, { target: { value: "__new__" } });
    expect(ed.newCharacter).toHaveBeenCalledTimes(1);
  });

  it("wires 削除 / 元に戻す / やり直し", () => {
    const ed = makeEd({
      history: { counts: { undo: 2, redo: 1 } } as CharacterEditor["history"],
    });
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(ed.deleteCurrent).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: /元に戻す/ }));
    expect(ed.undo).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: /やり直し/ }));
    expect(ed.redo).toHaveBeenCalledTimes(1);
  });

  // The name is held locally while it is being typed and only patched on blur,
  // so that every keystroke is not a round trip. Both halves matter.
  it("keeps the name local while typing and patches it on blur", async () => {
    const ed = makeEd();
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);
    const field = screen.getByRole("textbox", { name: "キャラクター名" });

    fireEvent.change(field, { target: { value: "Kira" } });
    expect(ed.setCh).toHaveBeenCalledWith(expect.objectContaining({ name: "Kira" }));
    expect(ed.patch).not.toHaveBeenCalled();

    fireEvent.blur(field, { target: { value: "Kira" } });
    expect(ed.patch).toHaveBeenCalledWith({ name: "Kira" });
    await waitFor(() => expect(ed.refreshRoster).toHaveBeenCalledTimes(1));
  });

  it("wires the three file exports and the import button", () => {
    const ed = makeEd();
    const fileRef = createRef<HTMLInputElement>();
    render(
      <Toolbar ed={ed} {...base} fileRef={fileRef} tab={"priority"} sheetLayout={"standard"} />,
    );

    fireEvent.click(screen.getByRole("button", { name: ".chum5書出" }));
    expect(ed.downloadChum5).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: ".xlsx書出" }));
    expect(ed.downloadXlsx).toHaveBeenCalledTimes(1);

    const click = vi.spyOn(fileRef.current!, "click");
    fireEvent.click(screen.getByRole("button", { name: "読込 (JSON/.chum5/.xlsx)" }));
    expect(click).toHaveBeenCalledTimes(1);

    const file = new File(["{}"], "x.json", { type: "application/json" });
    fireEvent.change(fileRef.current!, { target: { files: [file] } });
    expect(ed.onImport).toHaveBeenCalledWith(file);
  });

  it("copies the share link, the ココフォリア block and the chat palette under their own keys", () => {
    const ed = makeEd();
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);

    fireEvent.click(screen.getByRole("button", { name: "共有リンク" }));
    expect(ed.copyShareLink).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "ココフォリア" }));
    fireEvent.click(screen.getByRole("button", { name: "チャットパレット" }));
    // A block and a palette are different text; the second argument is what
    // decides which button shows コピー ✓, so swapping them would be
    // invisible without it.
    const [[block, blockKey], [palette, paletteKey]] = (ed.copyText as Mock).mock.calls;
    expect([blockKey, paletteKey]).toEqual(["cc", "cp"]);
    expect(typeof block).toBe("string");
    expect(block).not.toEqual(palette);
  });

  // The Udonarium export writes a file rather than copying, and the builder
  // needs the catalog and the translator — a wiring mistake there is silent.
  it("hands the Udonarium export the catalog, the translator and the untrained switch", () => {
    const ed = makeEd();
    render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);

    fireEvent.click(screen.getByRole("button", { name: "ユドナリウム" }));
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "ユドナリウム" }));

    const calls = (ed.downloadUdonarium as Mock).mock.calls;
    expect(calls).toHaveLength(2);
    expect(calls[0]).toEqual([base.catalog, ed.tr, { untrained: false }]);
    expect(calls[1]).toEqual([base.catalog, ed.tr, { untrained: true }]);
    // the switch is remembered in localStorage, which outlives this test
    fireEvent.click(screen.getByRole("checkbox"));
  });

  it("shows コピー ✓ on whichever button was copied, and no other", () => {
    render(
      <Toolbar ed={makeEd({ copied: "cc" })} {...base} tab={"priority"} sheetLayout={"standard"} />,
    );
    expect(screen.getByRole("button", { name: "コピー ✓" })).toBeDefined();
    expect(screen.getByRole("button", { name: "チャットパレット" })).toBeDefined();
    expect(screen.getByRole("button", { name: "共有リンク" })).toBeDefined();
  });

  // The untrained switch changes what the copied block holds, so it has to
  // reach the builder — not only flip the checkbox.
  it("feeds the untrained switch into the copied block", () => {
    const ed = makeEd();
    // The switch adds the *unlearned* skills, so the catalog has to hold one
    // for the two blocks to differ at all.
    const catalog = makeCatalog({
      skills: {
        skills: [
          {
            id: "s1",
            name: "Pistols",
            attribute: "AGI",
            category: "Combat Active",
            skillgroup: null,
            source: "SR5",
          },
        ],
        groups: [],
        knowledge: [],
      },
    });
    render(
      <Toolbar ed={ed} {...base} catalog={catalog} tab={"priority"} sheetLayout={"standard"} />,
    );
    const box = screen.getByRole("checkbox");

    fireEvent.click(screen.getByRole("button", { name: "ココフォリア" }));
    fireEvent.click(box);
    expect(box).toHaveProperty("checked", true);
    fireEvent.click(screen.getByRole("button", { name: "ココフォリア" }));

    const [[off], [on]] = (ed.copyText as Mock).mock.calls;
    expect(on).not.toEqual(off);
  });

  // The 召喚体 button is the only conditional one: nothing bound or registered,
  // nothing to copy.
  it("offers 召喚体 only once something is bound or registered", () => {
    render(<Toolbar ed={makeEd()} {...base} tab={"priority"} sheetLayout={"standard"} />);
    expect(screen.queryByRole("button", { name: "精霊コマ" })).toBeNull();

    const ed = makeEd();
    render(
      <Toolbar
        ed={ed}
        {...base}
        ch={makeCharacter({
          name: "Vex",
          derived: {
            spirits: [
              {
                id: "sp1",
                spirit_id: "fire",
                name: "Fire",
                force: 3,
                force_max: 6,
                services: 1,
                nuyen: 0,
                bound: true,
              },
            ],
          },
        })}
        tab={"priority"}
        sheetLayout={"standard"}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "精霊コマ" }));
    expect(ed.copyText).toHaveBeenCalledWith(expect.any(String), "cs");
  });

  it("asks before moving a character with creation errors into career mode", () => {
    const ed = makeEd();
    const ch = makeCharacter({ name: "Vex", derived: { errors: [{ key: "engine.oops" }] } });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    try {
      render(<Toolbar ed={ed} {...base} ch={ch} tab={"priority"} sheetLayout={"standard"} />);
      fireEvent.click(screen.getByRole("button", { name: "作成完了（キャリア）" }));
      expect(confirm).toHaveBeenCalledTimes(1);
      expect(ed.patch).not.toHaveBeenCalled();

      confirm.mockReturnValue(true);
      fireEvent.click(screen.getByRole("button", { name: "作成完了（キャリア）" }));
      expect(ed.patch).toHaveBeenCalledWith({ career: true });
    } finally {
      confirm.mockRestore();
    }
  });

  it("moves a clean character into career mode without asking, and back out", () => {
    const confirm = vi.spyOn(window, "confirm");
    try {
      const ed = makeEd();
      render(<Toolbar ed={ed} {...base} tab={"priority"} sheetLayout={"standard"} />);
      fireEvent.click(screen.getByRole("button", { name: "作成完了（キャリア）" }));
      expect(confirm).not.toHaveBeenCalled();
      expect(ed.patch).toHaveBeenCalledWith({ career: true });

      const back = makeEd();
      render(
        <Toolbar
          ed={back}
          {...base}
          ch={makeCharacter({ name: "Vex", career: true })}
          tab={"priority"}
          sheetLayout={"standard"}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: "キャリア中" }));
      expect(back.patch).toHaveBeenCalledWith({ career: false });
    } finally {
      confirm.mockRestore();
    }
  });

  it("wires the layout picker, 印刷 and シート表示", () => {
    const setSheetLayout = vi.fn();
    const setTab = vi.fn();
    const print = vi.spyOn(window, "print").mockImplementation(() => {});
    try {
      const { rerender } = render(
        <Toolbar
          ed={makeEd()}
          {...base}
          setSheetLayout={setSheetLayout}
          tab={"sheet"}
          sheetLayout={"standard"}
        />,
      );
      fireEvent.change(screen.getByRole("combobox", { name: "レイアウト" }), {
        target: { value: "compact" },
      });
      expect(setSheetLayout).toHaveBeenCalledWith("compact");

      // Not on `print` yet, so the button switches layout rather than printing.
      fireEvent.click(screen.getByRole("button", { name: "印刷 / PDF" }));
      expect(setSheetLayout).toHaveBeenCalledWith("print");
      expect(print).not.toHaveBeenCalled();

      rerender(
        <Toolbar
          ed={makeEd()}
          {...base}
          setSheetLayout={setSheetLayout}
          tab={"sheet"}
          sheetLayout={"print"}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: "印刷 / PDF" }));
      expect(print).toHaveBeenCalledTimes(1);

      rerender(
        <Toolbar
          ed={makeEd()}
          {...base}
          setTab={setTab}
          tab={"priority"}
          sheetLayout={"standard"}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: "シート表示" }));
      expect(setTab).toHaveBeenCalledWith("sheet");
    } finally {
      print.mockRestore();
    }
  });
});
