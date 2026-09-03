import type { MsgKey } from "@/lib/i18n/messages";
import type { Character } from "@/lib/types";

/**
 * Read-only share links. The whole character travels in the URL *fragment*
 * (`/share#c=<base64url of deflate-raw JSON>`), which browsers never put on
 * the wire — the backend, any proxy and any access log see only `/share`.
 * Nothing is stored server-side, which keeps the no-account model intact.
 *
 * The receiving page POSTs the payload to the stateless compute service to
 * get `derived` back, so a link stays valid across engine updates.
 */

/** Fragment key. `/share#c=…` */
export const SHARE_PREFIX = "#c=";

/** Envelope version. Bump when the payload shape needs a read-time migration. */
export const SHARE_VERSION = 1;

/**
 * What travels: the client-owned state minus what the receiver doesn't need.
 * `derived` is recomputed, `id` is reissued on adoption (a share must not
 * collide with a roster entry), and `portrait` is megabytes of base64 that
 * would not survive any URL.
 */
export type SharePayload = Omit<Character, "derived" | "id" | "portrait">;

/** Links longer than this survive a copy-paste but start getting mangled by
 *  chat clients and mail wrapping. Advisory only. */
export const SHARE_URL_WARN = 8_000;

/** Decompression-bomb guard: a 40-char fragment must not expand into 100MB. */
export const MAX_SHARE_BYTES = 4_000_000;

/** Why a share link could not be read (or built). */
export type ShareErrorCode = "corrupt" | "future" | "too-large" | "unsupported" | "empty";

/**
 * A share failure carrying a *code*, not a sentence. This module has no
 * locale — a share link is the one screen a visitor reaches with someone
 * else's settings, so the wording is looked up by the view that renders it.
 */
export class ShareError extends Error {
  constructor(readonly code: ShareErrorCode) {
    super(code);
    this.name = "ShareError";
  }
}

/** The message key for each failure. */
export const SHARE_ERROR_KEYS: Record<ShareErrorCode, MsgKey> = {
  corrupt: "share.err.corrupt",
  future: "share.err.future",
  "too-large": "share.err.tooLarge",
  unsupported: "share.err.unsupported",
  empty: "share.empty",
};

/**
 * A user-facing message for anything thrown while sharing. `ShareError` is
 * translated; anything else (a fetch failure, say) already carries a message,
 * and `fallback` covers the rest.
 */
export function shareErrorMessage(
  e: unknown,
  ui: (key: MsgKey) => string,
  fallback: MsgKey,
): string {
  if (e instanceof ShareError) return ui(SHARE_ERROR_KEYS[e.code]);
  if (e instanceof Error && e.message) return e.message;
  return ui(fallback);
}

const enc = new TextEncoder();
const dec = new TextDecoder();

function hasCompressionStreams(): boolean {
  return typeof CompressionStream !== "undefined" && typeof DecompressionStream !== "undefined";
}

/** True when this browser can build/read share links at all. */
export function shareSupported(): boolean {
  return hasCompressionStreams();
}

// typed as BufferSource because that is what `CompressionStream.writable`
// accepts in lib.dom; `pipeThrough` matches on the *input* chunk type.
function source(bytes: Uint8Array<ArrayBuffer>): ReadableStream<BufferSource> {
  return new ReadableStream<BufferSource>({
    start(c) {
      c.enqueue(bytes);
      c.close();
    },
  });
}

async function collect(
  stream: ReadableStream<Uint8Array>,
  cap: number,
): Promise<Uint8Array<ArrayBuffer>> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > cap) {
      await reader.cancel();
      throw new ShareError("too-large");
    }
    chunks.push(value);
  }
  const out = new Uint8Array(total);
  let at = 0;
  for (const c of chunks) {
    out.set(c, at);
    at += c.byteLength;
  }
  return out;
}

const deflate = (b: Uint8Array<ArrayBuffer>) =>
  collect(source(b).pipeThrough(new CompressionStream("deflate-raw")), MAX_SHARE_BYTES);

const inflate = (b: Uint8Array<ArrayBuffer>) =>
  collect(source(b).pipeThrough(new DecompressionStream("deflate-raw")), MAX_SHARE_BYTES);

function toBase64Url(bytes: Uint8Array): string {
  let bin = "";
  // chunked: String.fromCharCode(...huge) blows the argument limit
  for (let i = 0; i < bytes.length; i += 0x8000) {
    bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(text: string): Uint8Array<ArrayBuffer> {
  const b64 = text.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64 + "=".repeat((4 - (b64.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/** Strip the fields a share must not carry. */
export function toSharePayload(ch: Character): SharePayload {
  const { derived: _derived, id: _id, portrait: _portrait, ...rest } = ch;
  void _derived;
  void _id;
  void _portrait;
  return rest;
}

/** The fragment *value* (no `#c=`) for a character. */
export async function encodeShare(ch: Character): Promise<string> {
  if (!shareSupported()) throw new ShareError("unsupported");
  const json = JSON.stringify({ v: SHARE_VERSION, s: toSharePayload(ch) });
  return toBase64Url(await deflate(enc.encode(json)));
}

/**
 * A share payload from a fragment value. Everything here is attacker-supplied:
 * the size is capped above, the shape is checked here, and the backend's
 * Pydantic model is the real validator when the caller posts it to compute.
 */
export async function decodeShare(value: string): Promise<SharePayload> {
  if (!shareSupported()) throw new ShareError("unsupported");
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new ShareError("corrupt");

  let json: string;
  try {
    json = dec.decode(await inflate(fromBase64Url(value)));
  } catch (e) {
    if (e instanceof ShareError) throw e; // the size cap fired; say so, not "corrupt"
    throw new ShareError("corrupt");
  }

  let body: unknown;
  try {
    body = JSON.parse(json);
  } catch {
    throw new ShareError("corrupt");
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new ShareError("corrupt");
  }
  const { v, s } = body as { v?: unknown; s?: unknown };
  if (v !== SHARE_VERSION) throw new ShareError("future");
  if (!s || typeof s !== "object" || Array.isArray(s)) throw new ShareError("corrupt");

  // a hand-crafted link could still carry these; the receiver reissues both
  const { derived: _derived, id: _id, ...rest } = s as Record<string, unknown>;
  void _derived;
  void _id;
  return rest as SharePayload;
}

/** Full share URL for `character`, relative to `href` (usually `location.href`). */
export async function buildShareUrl(ch: Character, href: string): Promise<string> {
  const url = new URL("share", new URL(href).origin + "/");
  return `${url.href}${SHARE_PREFIX}${await encodeShare(ch)}`;
}

/** The fragment value in `hash`, or null when it carries no share payload. */
export function readShareValue(hash: string): string | null {
  return hash.startsWith(SHARE_PREFIX) ? hash.slice(SHARE_PREFIX.length) || null : null;
}
