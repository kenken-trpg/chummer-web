import { makeCharacter } from "@/tests/fixtures";
import {
  buildShareUrl,
  decodeShare,
  encodeShare,
  readShareValue,
  SHARE_ERROR_KEYS,
  SHARE_PREFIX,
  SHARE_VERSION,
  ShareError,
  shareErrorMessage,
  toSharePayload,
} from "@/lib/character/share";
import { MESSAGES, type MsgKey } from "@/lib/i18n/messages";

/** The `code` of the `ShareError` a promise rejects with. */
async function codeOf(p: Promise<unknown>): Promise<string> {
  try {
    await p;
  } catch (e) {
    if (e instanceof ShareError) return e.code;
    throw e;
  }
  throw new Error("expected a ShareError");
}

describe("toSharePayload", () => {
  it("drops derived, id and portrait but keeps the build", () => {
    const ch = makeCharacter({ id: "abc", name: "夜叉", portrait: "data:image/png;base64,AAAA" });
    const payload = toSharePayload(ch) as Record<string, unknown>;

    expect("derived" in payload).toBe(false);
    expect("id" in payload).toBe(false);
    expect("portrait" in payload).toBe(false);
    expect(payload.name).toBe("夜叉");
    expect(payload.metatype).toBe(ch.metatype);
  });
});

describe("encode / decode", () => {
  it("round-trips a character through the fragment", async () => {
    const ch = makeCharacter({ id: "x", name: "サムライ・ドッグ", notes: "コメント" });
    const decoded = (await decodeShare(await encodeShare(ch))) as Record<string, unknown>;

    expect(decoded.name).toBe("サムライ・ドッグ");
    expect(decoded.notes).toBe("コメント");
    expect("id" in decoded).toBe(false);
  });

  it("produces a base64url fragment (safe unescaped in a URL)", async () => {
    const value = await encodeShare(makeCharacter({ name: "夜叉" }));
    expect(value).toMatch(/^[A-Za-z0-9_-]+$/);
  });

  it("compresses — the fragment is smaller than the raw JSON", async () => {
    const ch = makeCharacter({ name: "Runner" });
    const value = await encodeShare(ch);
    expect(value.length).toBeLessThan(JSON.stringify(toSharePayload(ch)).length);
  });

  it("rejects a fragment with characters base64url never emits", async () => {
    expect(await codeOf(decodeShare("not base64!!"))).toBe("corrupt");
  });

  it("rejects a well-formed fragment that is not deflate data", async () => {
    expect(await codeOf(decodeShare("AAAAAAAA"))).toBe("corrupt");
  });

  it("rejects an envelope from a future version", async () => {
    // hand-build the envelope the way `encodeShare` does, with a bumped `v`
    const json = JSON.stringify({ v: SHARE_VERSION + 1, s: { name: "x" } });
    const src = new ReadableStream<BufferSource>({
      start(c) {
        c.enqueue(new TextEncoder().encode(json));
        c.close();
      },
    });
    const bytes = new Uint8Array(
      await new Response(src.pipeThrough(new CompressionStream("deflate-raw"))).arrayBuffer(),
    );
    let bin = "";
    for (const b of bytes) bin += String.fromCharCode(b);
    const value = btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

    expect(await codeOf(decodeShare(value))).toBe("future");
  });
});

describe("error messages", () => {
  it("has a ja *and* an en string for every failure code", () => {
    // a share link is opened with the visitor's locale, so `en` may not fall
    // back to `ja` here the way it may for the rest of the app chrome
    for (const key of Object.values(SHARE_ERROR_KEYS)) {
      expect(MESSAGES.ja[key], `ja ${key}`).toBeTruthy();
      expect(MESSAGES.en[key], `en ${key}`).toBeTruthy();
    }
  });

  it("translates a ShareError and passes other errors through", () => {
    const ui = (k: MsgKey) => `ui:${k}`;
    expect(shareErrorMessage(new ShareError("corrupt"), ui, "share.err.load")).toBe(
      "ui:share.err.corrupt",
    );
    expect(shareErrorMessage(new Error("boom"), ui, "share.err.load")).toBe("boom");
    expect(shareErrorMessage("???", ui, "share.err.load")).toBe("ui:share.err.load");
  });
});

describe("buildShareUrl / readShareValue", () => {
  it("points at /share on the same origin regardless of the current path", async () => {
    const url = await buildShareUrl(makeCharacter({ name: "夜叉" }), "https://example.test/deep/x");
    expect(url.startsWith(`https://example.test/share${SHARE_PREFIX}`)).toBe(true);
  });

  it("round-trips through the hash", async () => {
    const url = await buildShareUrl(makeCharacter({ name: "夜叉" }), "https://example.test/");
    const value = readShareValue(new URL(url).hash);
    expect(value).toBeTruthy();
    expect(((await decodeShare(value!)) as Record<string, unknown>).name).toBe("夜叉");
  });

  it("returns null for a hash with no payload", () => {
    expect(readShareValue("")).toBeNull();
    expect(readShareValue("#other=1")).toBeNull();
    expect(readShareValue(SHARE_PREFIX)).toBeNull();
  });
});
