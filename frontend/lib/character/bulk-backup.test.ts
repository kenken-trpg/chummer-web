import { isBulkBackup, readBulkBackup, writeBulkBackup, BULK_BACKUP_FORMAT } from "./bulk-backup";
import { makeCharacter } from "@/tests/fixtures";

it("round trips multiple full states, including names, notes and portraits", () => {
  const characters = [
    makeCharacter({ name: "同名", notes: "メモ", portrait: "data:image/png;base64,AA" }),
    makeCharacter({ id: "second", name: "同名", career: true }),
  ];
  const value = JSON.parse(writeBulkBackup(characters));
  expect(isBulkBackup(value)).toBe(true);
  expect(readBulkBackup(value).characters).toEqual(characters);
  expect(readBulkBackup(value).version).toBe(1);
});

it("distinguishes bulk files from single characters and rejects invalid or future files", () => {
  expect(isBulkBackup(makeCharacter())).toBe(false);
  expect(() => readBulkBackup({ format: BULK_BACKUP_FORMAT, version: 2 })).toThrow();
  expect(() =>
    readBulkBackup({ format: BULK_BACKUP_FORMAT, version: 1, createdAt: "bad", characters: [] }),
  ).toThrow();
  expect(() =>
    readBulkBackup({
      format: BULK_BACKUP_FORMAT,
      version: 1,
      createdAt: new Date().toISOString(),
      characters: [null],
    }),
  ).toThrow();
});
