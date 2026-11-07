import type { BackupStatus } from "./local-store";

export const BACKUP_CHANGE_THRESHOLD = 10;
export const BACKUP_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export function backupDue(status: BackupStatus, now = Date.now()): boolean {
  return (
    status.changesSinceBackup >= BACKUP_CHANGE_THRESHOLD ||
    (status.changesSinceBackup > 0 &&
      status.lastExportedAt !== null &&
      now - status.lastExportedAt >= BACKUP_AGE_MS)
  );
}
