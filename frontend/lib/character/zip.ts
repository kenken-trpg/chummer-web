/**
 * Just enough of the ZIP format to read a ruleset folder out of an archive.
 *
 * The folder picker (`webkitdirectory`) is how a published ruleset normally
 * arrives, and Android's Chrome does not implement it — there is no way to
 * hand a phone a folder. A `.zip` of the same folder is what a phone *can*
 * send, so it is read here into the same shape a directory pick produces.
 *
 * No library: the archive is a few hundred KB of XML, and the two things that
 * take work — inflate and the text decoding — are already in the platform.
 * `DecompressionStream("deflate-raw")` is the same primitive the share-link
 * codec uses.
 *
 * What is supported is what a folder zipped by Windows, macOS or `zip(1)`
 * produces: stored (method 0) and deflated (method 8) entries, in a plain
 * (non-ZIP64, unencrypted) archive. Anything else is reported rather than
 * half-read — a ruleset that merged three quarters of its house rules would
 * be worse than one that said it could not be opened.
 */

/** The archive is not a zip, or not one this can read. */
export class ZipError extends Error {
  constructor(readonly reason: "not-a-zip" | "unsupported" | "corrupt") {
    super(reason);
  }
}

/** Uncompressed bytes, per archive member. Directories are left out. */
export type ZipEntry = { path: string; bytes: Uint8Array<ArrayBuffer> };

const SIG_EOCD = 0x06054b50;
const SIG_CENTRAL = 0x02014b50;
const SIG_LOCAL = 0x04034b50;

/** The largest a zip comment may be, which bounds the backwards scan. */
const MAX_COMMENT = 0xffff;

/** A ceiling on what one member may inflate to, so a zip bomb cannot take the
 *  tab down. The largest thing Chummer ships is ~3 MB of XML. */
const MAX_ENTRY_BYTES = 64 * 1024 * 1024;

/** ZIP64 sentinels. Seeing one means the real value lives in an extra field
 *  this does not read. */
const U16_MAX = 0xffff;
const U32_MAX = 0xffffffff;

/**
 * Where the End of Central Directory record starts.
 *
 * Scanned backwards because its own length is variable: it ends with a comment
 * whose length is only known from inside it.
 */
function findEocd(view: DataView): number {
  const floor = Math.max(0, view.byteLength - MAX_COMMENT - 22);
  for (let at = view.byteLength - 22; at >= floor; at--) {
    if (view.getUint32(at, true) === SIG_EOCD) return at;
  }
  throw new ZipError("not-a-zip");
}

const utf8 = new TextDecoder("utf-8", { fatal: true });
const utf8Lossy = new TextDecoder("utf-8");

/**
 * A member's name.
 *
 * Bit 11 of the flags promises UTF-8, and everything that writes zips this
 * decade sets it. What does not is Windows Explorer on a Japanese system,
 * which writes the OEM code page instead — and a ruleset written in Japanese
 * has Japanese directory names, so this is the ordinary case here, not an
 * exotic one. UTF-8 is tried first either way (it is self-checking), and
 * Shift_JIS is the fallback that turns mojibake back into a path.
 */
function decodeName(bytes: Uint8Array, flags: number): string {
  if (flags & 0x800) return utf8Lossy.decode(bytes);
  try {
    return utf8.decode(bytes);
  } catch {
    try {
      return new TextDecoder("shift_jis", { fatal: true }).decode(bytes);
    } catch {
      return utf8Lossy.decode(bytes);
    }
  }
}

function inflateRaw(bytes: Uint8Array<ArrayBuffer>): Promise<Uint8Array<ArrayBuffer>> {
  const stream = new ReadableStream<BufferSource>({
    start(c) {
      c.enqueue(bytes);
      c.close();
    },
  }).pipeThrough(new DecompressionStream("deflate-raw"));
  return collect(stream);
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<Uint8Array<ArrayBuffer>> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_ENTRY_BYTES) {
      await reader.cancel();
      throw new ZipError("unsupported");
    }
    chunks.push(value);
  }
  const out = new Uint8Array(total);
  let at = 0;
  for (const chunk of chunks) {
    out.set(chunk, at);
    at += chunk.byteLength;
  }
  return out;
}

/** Every file in `data`, by path. Throws `ZipError` rather than returning a
 *  partial archive. */
export async function unzip(data: ArrayBuffer): Promise<ZipEntry[]> {
  const view = new DataView(data);
  const bytes = new Uint8Array(data);
  const slice = (from: number, to: number): Uint8Array<ArrayBuffer> => bytes.slice(from, to);
  if (data.byteLength < 22) throw new ZipError("not-a-zip");

  const eocd = findEocd(view);
  const count = view.getUint16(eocd + 10, true);
  const dirAt = view.getUint32(eocd + 16, true);
  // A multi-disk or ZIP64 archive: the numbers here are placeholders for ones
  // held elsewhere, so reading them would silently read the wrong bytes.
  if (count === U16_MAX || dirAt === U32_MAX) throw new ZipError("unsupported");
  if (dirAt + 46 > data.byteLength) throw new ZipError("corrupt");

  const out: ZipEntry[] = [];
  let at = dirAt;
  for (let i = 0; i < count; i++) {
    if (at + 46 > data.byteLength || view.getUint32(at, true) !== SIG_CENTRAL) {
      throw new ZipError("corrupt");
    }
    const flags = view.getUint16(at + 8, true);
    const method = view.getUint16(at + 10, true);
    const compressed = view.getUint32(at + 20, true);
    const nameLen = view.getUint16(at + 28, true);
    const extraLen = view.getUint16(at + 30, true);
    const commentLen = view.getUint16(at + 32, true);
    const localAt = view.getUint32(at + 42, true);
    const path = decodeName(bytes.subarray(at + 46, at + 46 + nameLen), flags);
    at += 46 + nameLen + extraLen + commentLen;

    // A directory entry, or a Windows/macOS housekeeping file. Skipping the
    // latter here keeps them out of the content hash the dataset is keyed by.
    const leaf = path.slice(path.lastIndexOf("/") + 1);
    if (path.endsWith("/") || path.startsWith("__MACOSX/") || leaf === ".DS_Store") continue;
    if (flags & 0x1) throw new ZipError("unsupported"); // encrypted
    if (compressed === U32_MAX || localAt === U32_MAX) throw new ZipError("unsupported");

    // The local header repeats the name and carries its own extra field, whose
    // length may differ from the central one's — so the data offset has to be
    // read from here rather than assumed.
    if (localAt + 30 > data.byteLength || view.getUint32(localAt, true) !== SIG_LOCAL) {
      throw new ZipError("corrupt");
    }
    const dataAt =
      localAt + 30 + view.getUint16(localAt + 26, true) + view.getUint16(localAt + 28, true);
    if (dataAt + compressed > data.byteLength) throw new ZipError("corrupt");
    const raw = slice(dataAt, dataAt + compressed);

    if (method === 0) out.push({ path, bytes: raw });
    else if (method === 8) out.push({ path, bytes: await inflateRaw(raw) });
    else throw new ZipError("unsupported");
  }
  return out;
}

/** Whether this browser can read a zip at all. Chrome 80, Safari 16.4,
 *  Firefox 113 — the same floor the share links already stand on. */
export function zipSupported(): boolean {
  return typeof DecompressionStream !== "undefined";
}
