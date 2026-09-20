/**
 * A zip, built in the test rather than checked in as a binary.
 *
 * Shared by the reader's own tests and by the settings panel's, so the panel
 * is driven with a real archive instead of a mocked reader.
 *
 * The reader ignores CRCs — a wrong one would have to be wrong in both the
 * archive and this builder to pass — so they are written as zero and the
 * builder stays short enough to read.
 */
export async function makeZip(
  entries: { name: string | Uint8Array; data: string; stored?: boolean }[],
  { utf8 = true } = {},
): Promise<ArrayBuffer> {
  const enc = new TextEncoder();
  const local: Uint8Array[] = [];
  const central: Uint8Array[] = [];
  let offset = 0;

  for (const entry of entries) {
    const name = typeof entry.name === "string" ? enc.encode(entry.name) : entry.name;
    const raw = enc.encode(entry.data);
    const body = entry.stored ? raw : await deflate(raw);
    const flags = utf8 ? 0x800 : 0;
    const method = entry.stored ? 0 : 8;

    const head = new DataView(new ArrayBuffer(30));
    head.setUint32(0, 0x04034b50, true);
    head.setUint16(6, flags, true);
    head.setUint16(8, method, true);
    head.setUint32(18, body.byteLength, true);
    head.setUint32(22, raw.byteLength, true);
    head.setUint16(26, name.byteLength, true);
    local.push(new Uint8Array(head.buffer), name, body);

    const dir = new DataView(new ArrayBuffer(46));
    dir.setUint32(0, 0x02014b50, true);
    dir.setUint16(8, flags, true);
    dir.setUint16(10, method, true);
    dir.setUint32(20, body.byteLength, true);
    dir.setUint32(24, raw.byteLength, true);
    dir.setUint16(28, name.byteLength, true);
    dir.setUint32(42, offset, true);
    central.push(new Uint8Array(dir.buffer), name);

    offset += 30 + name.byteLength + body.byteLength;
  }

  const dirBytes = concat(central);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true);
  end.setUint16(8, entries.length, true);
  end.setUint16(10, entries.length, true);
  end.setUint32(12, dirBytes.byteLength, true);
  end.setUint32(16, offset, true);
  const out = concat([concat(local), dirBytes, new Uint8Array(end.buffer)]);
  return out.buffer as ArrayBuffer;
}

export function concat(parts: Uint8Array[]): Uint8Array<ArrayBuffer> {
  const total = parts.reduce((n, p) => n + p.byteLength, 0);
  const out = new Uint8Array(total);
  let at = 0;
  for (const part of parts) {
    out.set(part, at);
    at += part.byteLength;
  }
  return out;
}

async function deflate(bytes: Uint8Array<ArrayBuffer>): Promise<Uint8Array> {
  const stream = new ReadableStream<BufferSource>({
    start(c) {
      c.enqueue(bytes);
      c.close();
    },
  }).pipeThrough(new CompressionStream("deflate-raw"));
  const chunks: Uint8Array[] = [];
  const reader = stream.getReader();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  return concat(chunks);
}
