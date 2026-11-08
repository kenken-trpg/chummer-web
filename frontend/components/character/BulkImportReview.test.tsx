import { fireEvent, render, screen } from "@testing-library/react";
import { BulkImportReview } from "./BulkImportReview";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr, makeCharacter } from "@/tests/fixtures";
import { writeBulkBackup, readBulkBackup } from "@/lib/character/bulk-backup";

it("shows selectable names and disables import for an empty selection", () => {
  const ed = {
    bulkImport: readBulkBackup(
      JSON.parse(
        writeBulkBackup([makeCharacter({ name: "Alpha" }), makeCharacter({ name: "Beta" })]),
      ),
    ),
    bulkSelection: [0, 1],
    bulkBusy: false,
    tr: identityTr,
    selectBulkImport: vi.fn(),
    confirmBulkImport: vi.fn(),
    cancelBulkImport: vi.fn(),
  } as unknown as CharacterEditor;
  const { rerender } = render(<BulkImportReview ed={ed} />);
  expect(screen.getAllByRole("checkbox")).toHaveLength(2);
  fireEvent.click(screen.getAllByRole("checkbox")[0]);
  expect(ed.selectBulkImport).toHaveBeenCalledWith([1]);
  fireEvent.click(screen.getByRole("button", { name: "選択したキャラクターを取り込む" }));
  expect(ed.confirmBulkImport).toHaveBeenCalledOnce();
  rerender(<BulkImportReview ed={{ ...ed, bulkSelection: [] }} />);
  expect(
    screen.getByRole("button", { name: "選択したキャラクターを取り込む" }).hasAttribute("disabled"),
  ).toBe(true);
});
