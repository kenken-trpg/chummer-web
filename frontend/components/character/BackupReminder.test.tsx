import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BackupReminder } from "./BackupReminder";
import { getBackupStatus } from "@/lib/character/local-store";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { makeCharacter } from "@/tests/fixtures";

vi.mock("@/lib/character/local-store", () => ({ getBackupStatus: vi.fn() }));

it("offers JSON backup when edits accumulate and refreshes after exporting", async () => {
  vi.mocked(getBackupStatus).mockResolvedValue({ lastExportedAt: null, changesSinceBackup: 10 });
  const download = vi.fn().mockResolvedValue(undefined);
  const ed = { ch: makeCharacter(), download, backupVersion: 0 } as unknown as CharacterEditor;
  const { rerender } = render(<BackupReminder ed={ed} />);
  await screen.findByRole("status");
  fireEvent.click(screen.getByRole("button", { name: "JSONでバックアップ" }));
  expect(download).toHaveBeenCalledOnce();
  vi.mocked(getBackupStatus).mockResolvedValue({
    lastExportedAt: Date.now(),
    changesSinceBackup: 0,
  });
  rerender(<BackupReminder ed={{ ...ed, backupVersion: 1 }} />);
  await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
  screen.getByText(/前回のJSON書き出し/);
});

it("never shows another character's reminder while switching", async () => {
  vi.mocked(getBackupStatus).mockResolvedValue({ lastExportedAt: null, changesSinceBackup: 10 });
  const ed = {
    ch: makeCharacter({ id: "a" }),
    download: vi.fn(),
    backupVersion: 0,
  } as unknown as CharacterEditor;
  const { rerender } = render(<BackupReminder ed={ed} />);
  await screen.findByRole("status");
  vi.mocked(getBackupStatus).mockReturnValue(new Promise(() => {}));
  rerender(<BackupReminder ed={{ ...ed, ch: makeCharacter({ id: "b" }) }} />);
  expect(screen.queryByRole("status")).toBeNull();
});
