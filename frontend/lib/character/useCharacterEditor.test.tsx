import { act, renderHook, waitFor } from "@testing-library/react";
import { makeCharacter } from "@/tests/fixtures";
import type { Catalog, Character } from "@/lib/types";
import { useCharacterEditor } from "@/lib/character/useCharacterEditor";
import { MESSAGES } from "@/lib/i18n/messages";
import { notify } from "@/lib/notices";

const catalog = { translations: { Ork: "オーク" } } as unknown as Catalog;

const api = vi.hoisted(() => ({
  catalog: vi.fn(),
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  remove: vi.fn(),
  patch: vi.fn(),
  compute: vi.fn(),
  import: vi.fn(),
  importChummer: vi.fn(),
  exportChummer: vi.fn(),
}));
vi.mock("@/lib/api", () => ({ api }));

beforeEach(() => {
  localStorage.clear();
  Object.values(api).forEach((fn) => fn.mockReset());
  api.catalog.mockResolvedValue(catalog);
  api.list.mockResolvedValue([]);
});

describe("useCharacterEditor", () => {
  it("bootstraps: loads the catalog and creates a fresh character when none is stored", async () => {
    const fresh = makeCharacter({ id: "c1", name: "Runner" });
    api.create.mockResolvedValue(fresh);

    const { result } = renderHook(() => useCharacterEditor());

    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));
    expect(api.create).toHaveBeenCalledWith("Runner");
    expect(result.current.catalog).toBe(catalog);
    expect(localStorage.getItem("lastCharacterId")).toBe("c1");
  });

  it("reopens the last character when its id is in the roster", async () => {
    localStorage.setItem("lastCharacterId", "saved");
    api.list.mockResolvedValue([{ id: "saved", name: "Saved" }]);
    api.get.mockResolvedValue(makeCharacter({ id: "saved", name: "Saved" }));

    const { result } = renderHook(() => useCharacterEditor());

    await waitFor(() => expect(result.current.ch?.id).toBe("saved"));
    expect(api.get).toHaveBeenCalledWith("saved");
    expect(api.create).not.toHaveBeenCalled();
  });

  it("patch records history and swaps in the server's character", async () => {
    const base = makeCharacter({ id: "c1", name: "Runner" });
    const patched = makeCharacter({ id: "c1", name: "Vex" });
    api.create.mockResolvedValue(base);
    api.patch.mockResolvedValue(patched);

    const { result } = renderHook(() => useCharacterEditor());
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    await act(async () => {
      await result.current.patch({ name: "Vex" });
    });

    expect(api.patch).toHaveBeenCalledWith("c1", { name: "Vex" });
    expect(result.current.ch?.name).toBe("Vex");
    expect(result.current.history.counts.undo).toBe(1);
  });

  it("undo recomputes the previous snapshot via api.compute", async () => {
    const base = makeCharacter({ id: "c1", name: "Runner" });
    const patched = makeCharacter({ id: "c1", name: "Vex" });
    api.create.mockResolvedValue(base);
    api.patch.mockResolvedValue(patched);
    api.compute.mockImplementation(async (snap: Character) => snap);

    const { result } = renderHook(() => useCharacterEditor());
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    await act(async () => {
      await result.current.patch({ name: "Vex" });
    });
    await act(async () => {
      await result.current.undo();
    });

    const snap = api.compute.mock.calls.at(-1)?.[0] as Character;
    expect(snap.id).toBe("c1");
    expect(snap.name).toBe("Runner");
    expect(result.current.ch?.name).toBe("Runner");
    expect(result.current.history.counts.undo).toBe(0);
    expect(result.current.history.counts.redo).toBe(1);
  });

  it("copyShareLink reports a dropped portrait as a notice, not an error", async () => {
    const base = makeCharacter({ id: "c1", portrait: "data:image/png;base64,AAAA" });
    api.create.mockResolvedValue(base);
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });

    const { result } = renderHook(() => useCharacterEditor());
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    await act(async () => {
      await result.current.copyShareLink();
    });

    expect(writeText.mock.calls[0][0]).toContain("/share#c=");
    expect(result.current.notice).toBe(MESSAGES.ja["share.portrait"]);
    expect(result.current.error).toBeNull();
  });

  it("reports a failed newCharacter instead of rejecting unhandled", async () => {
    api.create.mockResolvedValueOnce(makeCharacter({ id: "c1" }));
    const { result } = renderHook(() => useCharacterEditor());
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    api.create.mockRejectedValueOnce(new Error("バックエンドに接続できません"));
    let ok: boolean | undefined;
    await act(async () => {
      ok = await result.current.newCharacter();
    });

    expect(ok).toBe(false);
    expect(result.current.error).toBe("バックエンドに接続できません");
    expect(result.current.ch?.id).toBe("c1"); // still on the old one
  });

  it("surfaces a notice published by the api / storage layers", async () => {
    api.create.mockResolvedValue(makeCharacter({ id: "c1" }));
    const { result } = renderHook(() => useCharacterEditor());
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    act(() => notify("compute.offline"));

    expect(result.current.notice).toBe(MESSAGES.ja["compute.offline"]);
    expect(result.current.error).toBeNull();
  });

  it("onCharacterOpened fires after opening another character", async () => {
    const base = makeCharacter({ id: "c1" });
    api.create.mockResolvedValue(base);
    api.get.mockResolvedValue(makeCharacter({ id: "c2" }));
    const onCharacterOpened = vi.fn();

    const { result } = renderHook(() => useCharacterEditor({ onCharacterOpened }));
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));

    await act(async () => {
      await result.current.openCharacter("c2");
    });

    expect(result.current.ch?.id).toBe("c2");
    expect(onCharacterOpened).toHaveBeenCalledTimes(1);
  });
});
