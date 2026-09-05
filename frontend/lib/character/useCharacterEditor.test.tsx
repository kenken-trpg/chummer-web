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

/**
 * The rest of the hook: undo/redo, the two file exports, and the portrait
 * reader.
 *
 * Undo is the part with teeth. `busy.current` is a plain ref, not state, and
 * it is the only thing standing between a double-click and two overlapping
 * round trips — the second of which would restore a snapshot the first had
 * already stepped past. Nothing on screen shows the guard working, so the
 * only way it can be wrong is silently, by losing an edit.
 */

/** A promise plus the handle to settle it, for holding the hook mid-flight. */
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

async function booted(character = makeCharacter({ id: "c1", name: "Runner" })) {
  api.create.mockResolvedValue(character);
  const hook = renderHook(() => useCharacterEditor());
  await waitFor(() => expect(hook.result.current.ch?.id).toBe(character.id));
  return hook;
}

describe("useCharacterEditor undo/redo", () => {
  it("redo puts back what undo took away", async () => {
    const base = makeCharacter({ id: "c1", name: "Runner" });
    const patched = makeCharacter({ id: "c1", name: "Vex" });
    api.patch.mockResolvedValue(patched);
    api.compute.mockImplementation(async (snap: Character) => snap);
    const { result } = await booted(base);

    await act(async () => {
      await result.current.patch({ name: "Vex" });
    });
    await act(async () => {
      await result.current.undo();
    });
    expect(result.current.ch?.name).toBe("Runner");
    expect(result.current.history.counts.redo).toBe(1);

    await act(async () => {
      await result.current.redo();
    });
    expect(result.current.ch?.name).toBe("Vex");
    expect(result.current.history.counts.undo).toBe(1);
    expect(result.current.history.counts.redo).toBe(0);
  });

  it("does nothing when there is nothing to undo or redo", async () => {
    const { result } = await booted();

    await act(async () => {
      await result.current.undo();
      await result.current.redo();
    });

    expect(api.compute).not.toHaveBeenCalled();
    expect(result.current.error).toBeNull();
  });

  it("a second undo while the first is still in flight is ignored", async () => {
    // both would pop the stack, and the second would restore a snapshot the
    // first had already stepped past — an edit lost to a double-click
    const base = makeCharacter({ id: "c1", name: "Runner" });
    api.patch.mockResolvedValue(makeCharacter({ id: "c1", name: "Vex" }));
    const gate = deferred<Character>();
    api.compute.mockReturnValue(gate.promise);
    const { result } = await booted(base);

    await act(async () => {
      await result.current.patch({ name: "A" });
      await result.current.patch({ name: "B" });
    });
    expect(result.current.history.counts.undo).toBe(2);

    await act(async () => {
      const first = result.current.undo();
      const second = result.current.undo();
      gate.resolve(base);
      await Promise.all([first, second]);
    });

    expect(api.compute).toHaveBeenCalledTimes(1);
    expect(result.current.history.counts.undo).toBe(1);
  });

  it("a patch fired while one is in flight is dropped, not queued", async () => {
    const gate = deferred<Character>();
    api.patch.mockReturnValue(gate.promise);
    const { result } = await booted();

    await act(async () => {
      const first = result.current.patch({ name: "A" });
      const second = result.current.patch({ name: "B" });
      gate.resolve(makeCharacter({ id: "c1", name: "A" }));
      await Promise.all([first, second]);
    });

    expect(api.patch).toHaveBeenCalledTimes(1);
  });

  it("restoreSnapshot refuses to run while a patch is in flight", async () => {
    // undo and redo guard too, so this one is belt and braces -- but the hook
    // exposes restoreSnapshot, and a caller reaching it directly mid-patch
    // would overwrite the reply that is still on its way back
    const gate = deferred<Character>();
    api.patch.mockReturnValue(gate.promise);
    const base = makeCharacter({ id: "c1", name: "Runner" });
    const { result } = await booted(base);

    await act(async () => {
      const patching = result.current.patch({ name: "A" });
      await result.current.restoreSnapshot(base);
      gate.resolve(makeCharacter({ id: "c1", name: "A" }));
      await patching;
    });

    expect(api.compute).not.toHaveBeenCalled();
  });

  it("a failed undo says so and leaves the character where it was", async () => {
    const base = makeCharacter({ id: "c1", name: "Runner" });
    api.patch.mockResolvedValue(makeCharacter({ id: "c1", name: "Vex" }));
    // a message-less error: errorMessage() shows a thrown message verbatim
    // when there is one, so the fallback key is only reachable without it
    api.compute.mockRejectedValue(new Error(""));
    const { result } = await booted(base);

    await act(async () => {
      await result.current.patch({ name: "Vex" });
    });
    await act(async () => {
      await result.current.undo();
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.undo"]);
    expect(result.current.ch?.name).toBe("Vex");
  });
});

describe("useCharacterEditor file exports", () => {
  let clicks: { href: string; download: string }[];
  let blobs: Blob[];

  beforeEach(() => {
    clicks = [];
    blobs = [];
    // jsdom implements neither, and an <a download> click is a no-op there
    Object.assign(URL, {
      createObjectURL: vi.fn((blob: Blob) => {
        blobs.push(blob);
        return `blob:${blobs.length}`;
      }),
      revokeObjectURL: vi.fn(),
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clicks.push({ href: this.href, download: this.download });
    });
  });

  it("download() writes the character as JSON without asking the server", async () => {
    const { result } = await booted(makeCharacter({ id: "c1", name: "Vex" }));

    act(() => {
      result.current.download();
    });

    expect(clicks[0].download).toBe("Vex.json");
    expect(JSON.parse(await blobs[0].text()).name).toBe("Vex");
    expect(URL.revokeObjectURL).toHaveBeenCalledWith(clicks[0].href);
  });

  it("download() names an unnamed character something rather than nothing", async () => {
    const { result } = await booted(makeCharacter({ id: "c1", name: "" }));

    act(() => {
      result.current.download();
    });

    expect(clicks[0].download).toBe("character.json");
  });

  it("downloadChum5() saves the blob the server produced", async () => {
    api.exportChummer.mockResolvedValue(new Blob(["<character/>"]));
    const { result } = await booted(makeCharacter({ id: "c1", name: "Vex" }));

    await act(async () => {
      await result.current.downloadChum5();
    });

    expect(api.exportChummer).toHaveBeenCalledWith(result.current.ch);
    expect(clicks[0].download).toBe("Vex.chum5");
  });

  it("a refused .chum5 export is a message, not an unhandled rejection", async () => {
    api.exportChummer.mockRejectedValue(new Error(""));
    const { result } = await booted();

    await act(async () => {
      await result.current.downloadChum5();
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.export"]);
    expect(clicks).toHaveLength(0);
  });
});

describe("useCharacterEditor.onPortraitFile", () => {
  const image = (bytes: number, type = "image/png") =>
    new File([new Uint8Array(bytes)], "face.png", { type });

  it("refuses a file that is not an image before reading a byte of it", async () => {
    const { result } = await booted();

    await act(async () => {
      await result.current.onPortraitFile(new File(["x"], "notes.txt", { type: "text/plain" }));
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.notImage"]);
    expect(api.patch).not.toHaveBeenCalled();
  });

  it("refuses an image over 3MB", async () => {
    // it would be base64'd into the character and posted on every patch
    const { result } = await booted();

    await act(async () => {
      await result.current.onPortraitFile(image(3_000_001));
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.imageTooBig"]);
    expect(api.patch).not.toHaveBeenCalled();
  });

  it("patches an accepted image in as a data URL", async () => {
    api.patch.mockImplementation(async (_id: string, body: Record<string, unknown>) =>
      makeCharacter({ id: "c1", name: "Runner", ...body }),
    );
    const { result } = await booted();

    await act(async () => {
      await result.current.onPortraitFile(image(8));
    });

    const body = api.patch.mock.calls[0][1] as { portrait: string };
    expect(body.portrait.startsWith("data:image/png;base64,")).toBe(true);
  });

  it("turns an unreadable file into a message", async () => {
    const real = globalThis.FileReader;
    class Failing {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      error = new Error("");
      result = "";
      readAsDataURL() {
        this.onerror?.();
      }
    }
    globalThis.FileReader = Failing as unknown as typeof FileReader;
    try {
      const { result } = await booted();
      await act(async () => {
        await result.current.onPortraitFile(image(8));
      });
      expect(result.current.error).toBe(MESSAGES.ja["app.err.portraitRead"]);
    } finally {
      globalThis.FileReader = real;
    }
  });
});

describe("useCharacterEditor failure paths", () => {
  it("a catalog that will not load is reported, not swallowed", async () => {
    api.catalog.mockRejectedValue(new Error(""));

    const { result } = renderHook(() => useCharacterEditor());

    await waitFor(() => expect(result.current.error).toBe(MESSAGES.ja["app.err.boot"]));
    expect(result.current.ch).toBeNull();
  });

  it("a stored id that will not open falls back to a fresh character", async () => {
    // the record exists in the roster but is unreadable; booting into a null
    // character would leave the editor with nothing on screen
    localStorage.setItem("lastCharacterId", "saved");
    api.list.mockResolvedValue([{ id: "saved", name: "Saved" }]);
    api.get.mockRejectedValue(new Error("corrupt"));
    api.create.mockResolvedValue(makeCharacter({ id: "new", name: "Runner" }));

    const { result } = renderHook(() => useCharacterEditor());

    await waitFor(() => expect(result.current.ch?.id).toBe("new"));
    expect(result.current.error).toBeNull();
  });

  it("openCharacter reports a failure and keeps the current character", async () => {
    const { result } = await booted();
    api.get.mockRejectedValue(new Error(""));

    await act(async () => {
      await result.current.openCharacter("other");
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.load"]);
    expect(result.current.ch?.id).toBe("c1");
  });

  it("a failed duplicate is reported and opens nothing", async () => {
    const opened = vi.fn();
    api.create.mockResolvedValue(makeCharacter({ id: "c1", name: "Runner" }));
    const { result } = renderHook(() => useCharacterEditor({ onCharacterOpened: opened }));
    await waitFor(() => expect(result.current.ch?.id).toBe("c1"));
    opened.mockClear();
    vi.spyOn(window, "prompt").mockReturnValue("Copy");
    api.import.mockRejectedValue(new Error(""));

    await act(async () => {
      await result.current.duplicateCurrent();
    });

    expect(result.current.error).toBe(MESSAGES.ja["app.err.duplicate"]);
    expect(opened).not.toHaveBeenCalled();
  });

  it("a share link that cannot be built clears the notice left by the last one", async () => {
    // the notice is a caveat about a link that worked; leaving it up next to
    // a red error says the failed link has a dropped portrait
    const { result } = await booted(
      makeCharacter({ id: "c1", name: "Runner", portrait: "data:," }),
    );

    await act(async () => {
      await result.current.copyShareLink();
    });
    expect(result.current.notice).toBe(MESSAGES.ja["share.portrait"]);

    const ch = result.current.ch!;
    (ch as unknown as { self: unknown }).self = ch; // will not serialise
    await act(async () => {
      await result.current.copyShareLink();
    });

    expect(result.current.notice).toBeNull();
    expect(result.current.error).not.toBeNull();
  });
});
