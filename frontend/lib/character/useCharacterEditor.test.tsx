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
  // the real one returns local.deleteCharacter()'s promise, and deleteCurrent
  // chains .catch() onto it
  api.remove.mockResolvedValue(undefined);
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

/**
 * `onImport` is where a file written by another program enters the app. Every
 * layer under it is mocked in this suite, so what is left to pin is the part
 * the editor decides itself: which reader to use, and what the user is told
 * when the file is partly or wholly unusable.
 */
const file = (name: string, body = "{}") =>
  Object.assign(new File([body], name, { type: "application/json" }), {
    arrayBuffer: async () => new TextEncoder().encode(body).buffer,
    text: async () => body,
  }) as File;

/** Boot the editor with one character already open. */
async function editorWith(id = "c1") {
  api.create.mockResolvedValue(makeCharacter({ id }));
  const view = renderHook(() => useCharacterEditor());
  await waitFor(() => expect(view.result.current.ch?.id).toBe(id));
  return view;
}

describe("useCharacterEditor.onImport", () => {
  it.each([["run.chum5"], ["run.CHUM5"], ["run.chum5lz"]])(
    "sends %s to the Chummer reader, not the JSON one",
    async (name) => {
      const { result } = await editorWith();
      api.importChummer.mockResolvedValue({
        character: makeCharacter({ id: "imported" }),
        warnings: [],
      });

      await act(async () => {
        await result.current.onImport(file(name));
      });

      expect(api.importChummer).toHaveBeenCalledTimes(1);
      expect(api.import).not.toHaveBeenCalled();
      expect(result.current.ch?.id).toBe("imported");
    },
  );

  it("parses anything else as this app's own JSON", async () => {
    const { result } = await editorWith();
    api.import.mockResolvedValue(makeCharacter({ id: "imported" }));

    await act(async () => {
      await result.current.onImport(file("run.json", '{"name":"Vex"}'));
    });

    expect(api.import).toHaveBeenCalledWith({ name: "Vex" });
    expect(api.importChummer).not.toHaveBeenCalled();
    expect(result.current.ch?.id).toBe("imported");
  });

  it("opens the character even when the file had unsupported content", async () => {
    // the warnings ride the error channel, which makes this look like a
    // failure at a glance — it is not, and the character must still be open
    const { result } = await editorWith();
    api.importChummer.mockResolvedValue({
      character: makeCharacter({ id: "imported" }),
      warnings: ["unknown quality: Foo", "unknown gear: Bar"],
    });

    await act(async () => {
      await result.current.onImport(file("run.chum5"));
    });

    expect(result.current.ch?.id).toBe("imported");
    expect(result.current.error).toContain("2");
    expect(result.current.error).toContain("unknown quality: Foo");
  });

  it("caps the warning list rather than pasting hundreds into the UI", async () => {
    const { result } = await editorWith();
    const warnings = Array.from({ length: 40 }, (_, i) => `w${i}`);
    api.importChummer.mockResolvedValue({ character: makeCharacter({ id: "i" }), warnings });

    await act(async () => {
      await result.current.onImport(file("run.chum5"));
    });

    expect(result.current.error).toContain("40"); // the count is the true total
    expect(result.current.error).toContain("w14");
    expect(result.current.error).not.toContain("w15");
  });

  it("says nothing extra when the file imported cleanly", async () => {
    const { result } = await editorWith();
    api.importChummer.mockResolvedValue({ character: makeCharacter({ id: "i" }), warnings: [] });

    await act(async () => {
      await result.current.onImport(file("run.chum5"));
    });

    expect(result.current.error).toBeNull();
  });

  it("turns malformed JSON into a message instead of an unhandled rejection", async () => {
    const { result } = await editorWith();

    await act(async () => {
      await result.current.onImport(file("run.json", "{ not json"));
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.ch?.id).toBe("c1"); // the open character is untouched
    expect(api.import).not.toHaveBeenCalled();
  });

  it("clears a previous error before trying again", async () => {
    const { result } = await editorWith();
    await act(async () => {
      await result.current.onImport(file("bad.json", "{ not json"));
    });
    expect(result.current.error).toBeTruthy();

    api.import.mockResolvedValue(makeCharacter({ id: "ok" }));
    await act(async () => {
      await result.current.onImport(file("good.json", "{}"));
    });

    expect(result.current.error).toBeNull();
  });
});

describe("useCharacterEditor roster actions", () => {
  it("deleteCurrent opens the next character in the roster", async () => {
    const { result } = await editorWith();
    api.list.mockResolvedValue([
      { id: "c1", name: "One" },
      { id: "c2", name: "Two" },
    ]);
    await act(async () => await result.current.refreshRoster());
    api.get.mockResolvedValue(makeCharacter({ id: "c2" }));
    vi.spyOn(window, "confirm").mockReturnValue(true);

    await act(async () => await result.current.deleteCurrent());

    expect(api.remove).toHaveBeenCalledWith("c1");
    expect(result.current.ch?.id).toBe("c2");
  });

  it("deleting the last character mints a replacement rather than leaving none open", async () => {
    const { result } = await editorWith();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    api.create.mockResolvedValue(makeCharacter({ id: "replacement" }));

    await act(async () => await result.current.deleteCurrent());

    expect(result.current.ch?.id).toBe("replacement");
  });

  it("a declined confirm deletes nothing", async () => {
    const { result } = await editorWith();
    vi.spyOn(window, "confirm").mockReturnValue(false);

    await act(async () => await result.current.deleteCurrent());

    expect(api.remove).not.toHaveBeenCalled();
    expect(result.current.ch?.id).toBe("c1");
  });

  it("duplicateCurrent strips the id and derived, and takes the prompted name", async () => {
    const { result } = await editorWith();
    vi.spyOn(window, "prompt").mockReturnValue("Vex (copy)");
    api.import.mockResolvedValue(makeCharacter({ id: "dup" }));

    await act(async () => await result.current.duplicateCurrent());

    const sent = api.import.mock.calls[0][0] as Record<string, unknown>;
    expect(sent).not.toHaveProperty("id"); // a copy sharing an id would overwrite the original
    expect(sent).not.toHaveProperty("derived");
    expect(sent.name).toBe("Vex (copy)");
  });

  it("a cancelled duplicate prompt does nothing at all", async () => {
    const { result } = await editorWith();
    vi.spyOn(window, "prompt").mockReturnValue(null);

    await act(async () => await result.current.duplicateCurrent());

    expect(api.import).not.toHaveBeenCalled();
  });

  it("openCharacter ignores the id already open", async () => {
    const { result } = await editorWith();

    await act(async () => await result.current.openCharacter("c1"));

    expect(api.get).not.toHaveBeenCalled();
  });
});

describe("useCharacterEditor.copyText", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to execCommand when the clipboard API is denied", async () => {
    const { result } = await editorWith();
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText: () => Promise.reject(new Error("denied")) },
    });
    const exec = vi.fn().mockReturnValue(true);
    (document as unknown as { execCommand: unknown }).execCommand = exec;

    await act(async () => await result.current.copyText("text sheet", "text"));

    expect(exec).toHaveBeenCalledWith("copy");
    expect(result.current.copied).toBe("text"); // the button still confirms
    expect(document.querySelector("textarea")).toBeNull(); // and cleans up after itself
  });
});
