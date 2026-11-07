import { fireEvent, render, screen, within } from "@testing-library/react";
import { CharacterRoster } from "./CharacterRoster";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr, makeCharacter } from "@/tests/fixtures";

function editor() {
  return {
    ch: makeCharacter({ id: "a" }),
    tr: identityTr,
    refreshRoster: vi.fn(),
    openCharacter: vi.fn(),
    roster: [
      {
        id: "a",
        name: "Alpha",
        metatype: "Human",
        metavariant: "",
        talent: "Mundane",
        career: false,
        updated: 1000,
        buildMethod: "Priority",
        changesSinceBackup: 2,
      },
      {
        id: "b",
        name: "Beta",
        metatype: "Elf",
        metavariant: "",
        talent: "Magician",
        career: true,
        updated: 2000,
        buildMethod: "Karma",
        changesSinceBackup: 0,
      },
    ],
  } as unknown as CharacterEditor;
}

it("opens a searchable list and switches to the selected character", () => {
  const ed = editor();
  render(<CharacterRoster ed={ed} />);
  expect(screen.queryByRole("table")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "キャラクター一覧" }));
  expect(ed.refreshRoster).toHaveBeenCalledOnce();
  expect(
    screen.getByRole("button", { name: "Alpha（現在開いています）" }).hasAttribute("disabled"),
  ).toBe(true);
  screen.getByText("未バックアップの変更あり");
  screen.getByText("Karma");
  fireEvent.change(screen.getByRole("searchbox", { name: "名前で検索" }), {
    target: { value: "BETA" },
  });
  expect(screen.queryByText("Alpha")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Betaを開く" }));
  expect(ed.openCharacter).toHaveBeenCalledWith("b");
});

it("filters by state, sorts and reports empty results", () => {
  render(<CharacterRoster ed={editor()} />);
  fireEvent.click(screen.getByRole("button", { name: "キャラクター一覧" }));
  expect(within(screen.getAllByRole("row")[1]).getByText("Beta")).toBeTruthy();
  fireEvent.change(screen.getByRole("combobox", { name: "並べ替え" }), {
    target: { value: "name" },
  });
  expect(within(screen.getAllByRole("row")[1]).getByText("Alpha")).toBeTruthy();
  fireEvent.change(screen.getByRole("combobox", { name: "状態" }), { target: { value: "career" } });
  expect(screen.queryByText("Alpha")).toBeNull();
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "missing" } });
  screen.getByText("条件に一致するキャラクターがありません。");
  expect(screen.queryByRole("table")).toBeNull();
});
