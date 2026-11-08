import { act, renderHook } from "@testing-library/react";
import { useCharacterExport } from "./useCharacterExport";
import { recordBackup, getAllCharacters } from "./local-store";
import { api } from "@/lib/api";
import { useUiText } from "@/lib/i18n";
import { makeCharacter } from "@/tests/fixtures";

vi.mock("./local-store", () => ({ recordBackup: vi.fn(), getAllCharacters: vi.fn() }));
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

function boot(waitForIdle?: () => Promise<void>) {
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
      waitForIdle,
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

it("backs up every saved character after waiting for edits and records each JSON backup", async () => {
  const characters = [makeCharacter({ id: "all-a" }), makeCharacter({ id: "all-b" })];
  vi.mocked(getAllCharacters).mockResolvedValue(characters);
  let finishEdits!: () => void;
  const idle = new Promise<void>((resolve) => {
    finishEdits = resolve;
  });
  const { result } = boot(() => idle);
  let download!: Promise<void>;
  act(() => {
    download = result.current.downloadAll();
  });
  expect(getAllCharacters).not.toHaveBeenCalled();
  await act(async () => {
    finishEdits();
    await download;
  });
  const blob = vi.mocked(URL.createObjectURL).mock.calls[0][0] as Blob;
  expect(JSON.parse(await blob.text()).characters).toEqual(characters);
  expect(getAllCharacters).toHaveBeenCalledOnce();
  expect(recordBackup).toHaveBeenCalledTimes(2);
  expect(recordBackup).toHaveBeenCalledWith(characters[0]);
  expect(recordBackup).toHaveBeenCalledWith(characters[1]);
  expect(result.current.backupVersion).toBe(1);
});
