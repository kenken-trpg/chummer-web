import type { Character } from "@/lib/types";
import { MessageError } from "@/lib/errors";

export const BULK_BACKUP_FORMAT = "chummer-web-backup";
export type BulkBackup = {
  format: typeof BULK_BACKUP_FORMAT;
  version: 1;
  createdAt: string;
  characters: Array<{ name: string; metatype: string; career?: boolean } & Record<string, unknown>>;
};

export function isBulkBackup(value: unknown): boolean {
  return (
    !!value && typeof value === "object" && "format" in value && value.format === BULK_BACKUP_FORMAT
  );
}

export function readBulkBackup(value: unknown): BulkBackup {
  if (!isBulkBackup(value)) throw new MessageError("app.bulk.invalid");
  const backup = value as Partial<BulkBackup>;
  if (backup.version !== 1) throw new MessageError("app.bulk.version");
  if (
    typeof backup.createdAt !== "string" ||
    !Number.isFinite(Date.parse(backup.createdAt)) ||
    !Array.isArray(backup.characters) ||
    !backup.characters.length ||
    !backup.characters.every(
      (c) =>
        c &&
        typeof c === "object" &&
        !Array.isArray(c) &&
        typeof c.name === "string" &&
        typeof c.metatype === "string",
    )
  ) {
    throw new MessageError("app.bulk.invalid");
  }
  return backup as BulkBackup;
}

export function writeBulkBackup(characters: Character[]): string {
  return JSON.stringify(
    { format: BULK_BACKUP_FORMAT, version: 1, createdAt: new Date().toISOString(), characters },
    null,
    2,
  );
}
