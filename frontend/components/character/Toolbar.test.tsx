import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { Toolbar } from "@/components/character/Toolbar";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

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
    copyText: vi.fn(),
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
});
