import { act, renderHook } from "@testing-library/react";
import { useCharacterImport } from "./useCharacterImport";
import { writeBulkBackup } from "./bulk-backup";
import { addCharacters } from "./local-store";
import { api } from "@/lib/api";
import { useUiText } from "@/lib/i18n";
import { makeCharacter } from "@/tests/fixtures";

vi.mock("./local-store", () => ({ addCharacters: vi.fn() }));
vi.mock("@/lib/api", () => ({ api: { preview: vi.fn(), import: vi.fn() } }));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(addCharacters).mockResolvedValue(undefined);
});
const first = makeCharacter({ id: "old-a", name: "Alpha" });
const second = makeCharacter({ id: "old-b", name: "Beta" });
const file = { name: "backup.json", text: async () => writeBulkBackup([first, second]) } as File;
function boot() {
  const remember = vi.fn().mockResolvedValue(undefined);
  const setError = vi.fn();
  const setNotice = vi.fn();
  const refreshRoster = vi.fn().mockResolvedValue(undefined);
  const result = renderHook(() => {
    const { ui } = useUiText();
    return useCharacterImport({ ch: first, ui, remember, setError, setNotice, refreshRoster });
  });
  return { ...result, remember, setError, setNotice };
}

it("waits for selection and imports only selected characters as new copies", async () => {
  const { result, remember, setNotice } = boot();
  await act(async () => {
    await result.current.onImport(file);
  });
  expect(api.preview).not.toHaveBeenCalled();
  expect(api.import).not.toHaveBeenCalled();
  expect(result.current.bulkSelection).toEqual([0, 1]);
  act(() => result.current.selectBulkImport([1]));
  const copy = makeCharacter({ id: "fresh-b", name: "Beta" });
  vi.mocked(api.preview).mockResolvedValueOnce(copy);
  await act(async () => {
    await result.current.confirmBulkImport();
  });
  expect(api.preview).toHaveBeenCalledExactlyOnceWith(second);
  expect(addCharacters).toHaveBeenCalledExactlyOnceWith([copy]);
  expect(remember).toHaveBeenCalledWith(copy);
  expect(result.current.bulkImport).toBeNull();
  expect(setNotice).toHaveBeenCalledWith("1人のキャラクターを取り込みました。");
});

it("does not persist anything when one selected character fails validation", async () => {
  const { result, setError } = boot();
  await act(async () => {
    await result.current.onImport(file);
  });
  vi.mocked(api.preview)
    .mockResolvedValueOnce(makeCharacter({ id: "new-a" }))
    .mockRejectedValueOnce(new Error("Invalid character"));
  await act(async () => {
    await result.current.confirmBulkImport();
  });
  expect(addCharacters).not.toHaveBeenCalled();
  expect(result.current.bulkImport).not.toBeNull();
  expect(result.current.bulkBusy).toBe(false);
  expect(setError).toHaveBeenLastCalledWith(expect.stringContaining("Invalid character"));
});

it("can cancel and does nothing when no characters are selected", async () => {
  const { result } = boot();
  await act(async () => {
    await result.current.onImport(file);
  });
  act(() => result.current.selectBulkImport([]));
  await act(async () => {
    await result.current.confirmBulkImport();
  });
  expect(addCharacters).not.toHaveBeenCalled();
  act(() => result.current.cancelBulkImport());
  expect(result.current.bulkImport).toBeNull();
});
