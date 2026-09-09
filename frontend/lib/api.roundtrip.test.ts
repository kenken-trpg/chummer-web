import "fake-indexeddb/auto";

import { makeCharacter } from "@/tests/fixtures";
import { api } from "@/lib/api";
import * as local from "@/lib/character/local-store";
import { MessageError } from "@/lib/errors";
import { onNotice } from "@/lib/notices";
import { putCustomData } from "@/lib/character/customdata-store";

/**
 * `api.ts` is the whole client/server boundary now that the backend keeps
 * nothing: every method reads or writes the local store around a fetch. Its
 * sibling `api.test.ts` covers `errorText`; this covers the methods, against a
 * real IndexedDB and a stubbed `fetch`, because the interesting behaviour is
 * exactly which of the two sides gets touched on each path.
 */

type Call = { path: string; init: RequestInit | undefined };

let calls: Call[] = [];
let respond: (path: string) => Response | Promise<Response>;

function json(body: unknown, ok = true, status = 200): Response {
  const res = {
    ok,
    status,
    statusText: "",
    json: async () => body,
    text: async () => JSON.stringify(body),
    blob: async () => new Blob([JSON.stringify(body)]),
    headers: { get: () => "application/json" },
    // a real Response has this, and the custom-data retry reads the body
    // before `errorText` may read it again
    clone: () => json(body, ok, status),
  } as unknown as Response;
  return res;
}

beforeEach(async () => {
  calls = [];
  respond = () => json({});
  vi.stubGlobal("fetch", (path: string, init?: RequestInit) => {
    calls.push({ path, init });
    return Promise.resolve(respond(path));
  });
  for (const row of await local.listCharacters()) await local.deleteCharacter(row.id);
});

afterEach(() => {
  vi.unstubAllGlobals();
  onNotice(null);
});

const body = (call: Call) => JSON.parse(String(call.init?.body));

describe("api.create / api.patch", () => {
  it("stores what the engine returns, so a reload finds it", async () => {
    const fresh = makeCharacter({ id: "server-id", name: "Runner" });
    respond = () => json(fresh);

    const created = await api.create("Runner");

    expect(created).toEqual(fresh);
    expect(await local.getCharacter("server-id")).toEqual(fresh);
  });

  it("posts the stored state alongside the patch, not the patch alone", async () => {
    const stored = makeCharacter({ id: "a", name: "Before" });
    await local.putCharacter(stored);
    respond = () => json(makeCharacter({ id: "a", name: "After" }));

    await api.patch("a", { name: "After" });

    expect(calls[0].path).toBe("/api/characters/patch");
    expect(body(calls[0])).toEqual({ state: stored, patch: { name: "After" } });
    expect((await local.getCharacter("a"))?.name).toBe("After");
  });

  it("refuses to patch an id the browser does not hold", async () => {
    // the server has no roster to fall back on, so this cannot be recovered
    await expect(api.patch("ghost", { name: "x" })).rejects.toBeInstanceOf(MessageError);
    expect(calls).toEqual([]);
  });

  it("leaves the stored copy alone when the engine rejects the patch", async () => {
    const stored = makeCharacter({ id: "a", name: "Before" });
    await local.putCharacter(stored);
    respond = () => json({ detail: "invalid" }, false, 422);

    await expect(api.patch("a", { name: "" })).rejects.toThrow("invalid");
    expect(await local.getCharacter("a")).toEqual(stored);
  });
});

describe("api.get", () => {
  it("recomputes `derived` against the current engine and keeps the result", async () => {
    const stale = makeCharacter({ id: "a", name: "Jazz" });
    await local.putCharacter(stale);
    const recomputed = { ...stale, derived: { ...stale.derived, armor: 12 } };
    respond = () => json(recomputed);

    expect((await api.get("a")).derived.armor).toBe(12);
    expect((await local.getCharacter("a"))?.derived.armor).toBe(12);
  });

  it("falls back to the stored copy when the engine is unreachable, and says so", async () => {
    const stored = makeCharacter({ id: "a", name: "Jazz" });
    await local.putCharacter(stored);
    respond = () => Promise.reject(new Error("offline"));
    const seen: string[] = [];
    onNotice((key) => seen.push(key));

    // the sheet still renders; silence here would show numbers from an older
    // engine with nothing to say they are old
    expect(await api.get("a")).toEqual(stored);
    expect(seen).toEqual(["compute.offline"]);
  });

  it("reports a missing id as a coded error, not a 404 from the server", async () => {
    await expect(api.get("ghost")).rejects.toBeInstanceOf(MessageError);
  });
});

describe("api.preview / api.import", () => {
  it("preview computes without joining the roster", async () => {
    const foreign = makeCharacter({ id: "reissued", name: "From a link" });
    respond = () => json(foreign);

    expect(await api.preview({ name: "From a link" })).toEqual(foreign);

    expect(await local.getCharacter("reissued")).toBeNull();
    expect(await local.listCharacters()).toEqual([]);
  });

  it("import is preview plus the write", async () => {
    const foreign = makeCharacter({ id: "reissued", name: "From a link" });
    respond = () => json(foreign);

    await api.import({ name: "From a link" });

    expect(await local.getCharacter("reissued")).toEqual(foreign);
  });

  it("importChummer keeps the warnings and stores the character", async () => {
    const character = makeCharacter({ id: "chum", name: "Imported" });
    respond = () => json({ character, warnings: ["dropped 2 unknown qualities"] });

    const res = await api.importChummer(new ArrayBuffer(8));

    expect(res.warnings).toEqual(["dropped 2 unknown qualities"]);
    expect(await local.getCharacter("chum")).toEqual(character);
    expect(calls[0].init?.headers).toMatchObject({
      "Content-Type": "application/octet-stream",
    });
  });
});

describe("api.list / api.remove / api.compute", () => {
  it("list is local only — no request goes out", async () => {
    await local.putCharacter(makeCharacter({ id: "a", name: "Jazz" }));

    expect((await api.list()).map((r) => r.name)).toEqual(["Jazz"]);
    expect(calls).toEqual([]);
  });

  it("remove is local only", async () => {
    await local.putCharacter(makeCharacter({ id: "a" }));

    await api.remove("a");

    expect(await local.getCharacter("a")).toBeNull();
    expect(calls).toEqual([]);
  });

  it("compute posts a state verbatim, with no patch (undo/redo restore)", async () => {
    const snapshot = makeCharacter({ id: "a", name: "Two steps back" });
    respond = () => json(snapshot);

    await api.compute(snapshot);

    expect(body(calls[0])).toEqual({ state: snapshot });
    expect(await local.getCharacter("a")).toEqual(snapshot);
  });
});

describe("api.exportChummer", () => {
  it("returns the blob and writes nothing to the roster", async () => {
    const state = makeCharacter({ id: "a" });
    respond = () => json("<character/>");

    expect(await api.exportChummer(state)).toBeInstanceOf(Blob);
    expect(await local.listCharacters()).toEqual([]);
  });

  it("surfaces the server's message rather than a bare status", async () => {
    respond = () => json({ detail: "request body too large" }, false, 413);

    await expect(api.exportChummer(makeCharacter({ id: "a" }))).rejects.toThrow(
      "request body too large",
    );
  });
});

describe("the custom-data handshake", () => {
  /**
   * The browser holds the `customdata/` files and sends only their hash. A
   * server that has never seen that hash — or has evicted it — answers 409;
   * `req` uploads the set and repeats the request. None of the callers know.
   */
  const state = makeCharacter({
    id: "c1",
    settings: { name: "House", books: [], customdata: ["g>1"], dataset: "hash1" },
  });

  it("uploads the stored files and retries the request once", async () => {
    await local.putCharacter(state);
    await putCustomData("hash1", { "d/custom_x.xml": "<chummer/>" });

    let served = false;
    respond = (path) => {
      if (path === "/api/customdata") return json({ dataset: "hash1", applied: 1, skipped: [] });
      if (!served) {
        served = true;
        return json(
          { detail: { key: "api.customDataMissing", params: { dataset: "hash1" } } },
          false,
          409,
        );
      }
      return json({ ...state, name: "Merged" });
    };

    expect(await api.patch("c1", { name: "Merged" })).toMatchObject({ name: "Merged" });
    expect(calls.map((c) => c.path)).toEqual([
      "/api/characters/patch",
      "/api/customdata",
      "/api/characters/patch",
    ]);
    // the upload carries the directories the character asks for, in order
    expect(body(calls[1])).toEqual({
      files: { "d/custom_x.xml": "<chummer/>" },
      customdata: ["g>1"],
    });
  });

  it("gives up rather than looping when the files are not in this browser", async () => {
    await local.putCharacter(
      makeCharacter({
        id: "c2",
        settings: { name: "H", books: [], customdata: ["g>1"], dataset: "gone" },
      }),
    );
    respond = () =>
      json({ detail: { key: "api.customDataMissing", params: { dataset: "gone" } } }, false, 409);

    await expect(api.patch("c2", { name: "x" })).rejects.toThrow();
    // one attempt, no upload: there was nothing to upload
    expect(calls.map((c) => c.path)).toEqual(["/api/characters/patch"]);
  });

  it("retries at most once, so a server that keeps refusing surfaces the error", async () => {
    await local.putCharacter(state);
    await putCustomData("hash1", { "d/custom_x.xml": "<chummer/>" });
    respond = (path) =>
      path === "/api/customdata"
        ? json({ dataset: "hash1", applied: 1, skipped: [] })
        : json(
            { detail: { key: "api.customDataMissing", params: { dataset: "hash1" } } },
            false,
            409,
          );

    await expect(api.patch("c1", { name: "x" })).rejects.toThrow();
    expect(calls.filter((c) => c.path === "/api/customdata")).toHaveLength(1);
  });
});
