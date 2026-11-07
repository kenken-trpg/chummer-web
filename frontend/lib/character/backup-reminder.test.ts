import { backupDue, BACKUP_AGE_MS } from "./backup-reminder";

it("reminds at ten changes, including when there has never been a backup", () => {
  expect(backupDue({ lastExportedAt: null, changesSinceBackup: 9 })).toBe(false);
  expect(backupDue({ lastExportedAt: null, changesSinceBackup: 10 })).toBe(true);
});

it("reminds after seven days only when there are changes", () => {
  const at = 1000;
  expect(backupDue({ lastExportedAt: at, changesSinceBackup: 1 }, at + BACKUP_AGE_MS - 1)).toBe(
    false,
  );
  expect(backupDue({ lastExportedAt: at, changesSinceBackup: 1 }, at + BACKUP_AGE_MS)).toBe(true);
  expect(backupDue({ lastExportedAt: at, changesSinceBackup: 0 }, at + BACKUP_AGE_MS)).toBe(false);
});
