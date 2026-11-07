import { act, renderHook } from "@testing-library/react";
import { useCharacterExport } from "./useCharacterExport";
import { recordBackup } from "./local-store";
import { api } from "@/lib/api";
import { useUiText } from "@/lib/i18n";
import { makeCharacter } from "@/tests/fixtures";

vi.mock("./local-store", () => ({ recordBackup: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { checkChummerExport: vi.fn(), exportChummer: vi.fn() } }));

beforeEach(() => {
  vi.mocked(recordBackup).mockResolvedValue(true);
  vi.stubGlobal("URL", {
    createObjectURL: vi.fn().mockReturnValue("blob:test"),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

function boot() {
  const character = makeCharacter({ id: "backup-export" });
  const setNotice = vi.fn();
  const setError = vi.fn();
  const result = renderHook(() => {
    const { ui } = useUiText();
    return useCharacterExport({
      ch: character,
      ui,
      locale: "ja",
      pendingGearCount: 0,
      setNotice,
      setError,
    });
  });
  return { ...result, character, setNotice, setError };
}

it("records the exact JSON export and refreshes the backup status", async () => {
  const { result, character } = boot();
  await act(async () => {
    await result.current.download();
  });
  expect(recordBackup).toHaveBeenCalledWith(character);
  expect(result.current.backupVersion).toBe(1);
});

it("does not record a download that could not be offered", async () => {
  vi.mocked(URL.createObjectURL).mockImplementation(() => {
    throw new Error("Download failed");
  });
  const { result, setError } = boot();
  await act(async () => {
    await result.current.download();
  });
  expect(recordBackup).not.toHaveBeenCalled();
  expect(setError).toHaveBeenCalled();
  expect(result.current.backupVersion).toBe(0);
});

it("reports metadata failure without resetting the reminder", async () => {
  vi.mocked(recordBackup).mockRejectedValue(new Error("storage unavailable"));
  const { result, setNotice } = boot();
  await act(async () => {
    await result.current.download();
  });
  expect(setNotice).toHaveBeenCalledWith(
    expect.stringContaining("書き出し日時を記録できませんでした"),
  );
  expect(result.current.backupVersion).toBe(0);
});

it("does not mark Chummer exports as JSON backups", async () => {
  vi.mocked(api.checkChummerExport).mockResolvedValue([]);
  vi.mocked(api.exportChummer).mockResolvedValue(new Blob(["<character/>"]));
  const { result } = boot();
  await act(async () => {
    await result.current.downloadChum5();
  });
  expect(recordBackup).not.toHaveBeenCalled();
});
