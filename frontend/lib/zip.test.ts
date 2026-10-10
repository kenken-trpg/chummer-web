import { crc32, zipFiles, zipSingleFile } from "@/lib/zip";

const u8 = (b: Blob) => b.arrayBuffer().then((a) => new Uint8Array(a));

describe("crc32", () => {
  // the standard check value: CRC-32 of "123456789"
  it("matches the IEEE check value", () => {
    expect(crc32(new TextEncoder().encode("123456789"))).toBe(0xcbf43926);
  });
});

describe("zipSingleFile", () => {
  it("writes the three records a reader looks for, in order", async () => {
    const bytes = await u8(zipSingleFile("data.xml", "<x/>"));
    const sig = (at: number) => new DataView(bytes.buffer, bytes.byteOffset).getUint32(at, true);
    expect(sig(0)).toBe(0x04034b50); // local file header
    expect(sig(bytes.length - 22)).toBe(0x06054b50); // end of central directory
    // the central directory sits where the end record says it does
    const end = new DataView(bytes.buffer, bytes.byteOffset + bytes.length - 22);
    expect(sig(end.getUint32(16, true))).toBe(0x02014b50);
    expect(end.getUint16(10, true)).toBe(1); // one entry
  });

  it("stores the content verbatim, with its length and checksum", async () => {
    const content = "<character>ゴースト</character>";
    const data = new TextEncoder().encode(content);
    const bytes = await u8(zipSingleFile("data.xml", content));
    const view = new DataView(bytes.buffer, bytes.byteOffset);
    expect(view.getUint16(8, true)).toBe(0); // method: stored
    expect(view.getUint32(14, true)).toBe(crc32(data));
    expect(view.getUint32(22, true)).toBe(data.length);
    // stored, so the bytes are in there as they are, right after name + header
    const start = 30 + "data.xml".length;
    expect(new TextDecoder().decode(bytes.slice(start, start + data.length))).toBe(content);
  });

  it("flags the entry name as UTF-8, so a non-ASCII name survives", async () => {
    const bytes = await u8(zipSingleFile("コマ.xml", "<x/>"));
    const view = new DataView(bytes.buffer, bytes.byteOffset);
    expect(view.getUint16(6, true) & 0x0800).toBe(0x0800);
    const nameLen = view.getUint16(26, true);
    expect(new TextDecoder().decode(bytes.slice(30, 30 + nameLen))).toBe("コマ.xml");
  });
});

describe("zipFiles", () => {
  it("writes every entry, and points the directory at each one's own header", async () => {
    const files = [
      { name: "data.xml", content: "<a/>" },
      { name: "data_1.xml", content: "<bb/>" },
      { name: "data_2.xml", content: "<ccc/>" },
    ];
    const bytes = await u8(zipFiles(files));
    const view = new DataView(bytes.buffer, bytes.byteOffset);
    const end = new DataView(bytes.buffer, bytes.byteOffset + bytes.length - 22);
    expect(end.getUint16(10, true)).toBe(3);

    // walk the central directory and check each entry's offset lands on a
    // local header holding that entry's name
    let at = end.getUint32(16, true);
    for (const file of files) {
      expect(view.getUint32(at, true)).toBe(0x02014b50);
      const nameLen = view.getUint16(at + 28, true);
      const local = view.getUint32(at + 42, true);
      expect(view.getUint32(local, true)).toBe(0x04034b50);
      const localNameLen = view.getUint16(local + 26, true);
      expect(new TextDecoder().decode(bytes.slice(local + 30, local + 30 + localNameLen))).toBe(
        file.name,
      );
      const size = view.getUint32(local + 22, true);
      const start = local + 30 + localNameLen;
      expect(new TextDecoder().decode(bytes.slice(start, start + size))).toBe(file.content);
      at += 46 + nameLen;
    }
  });

  it("writes an empty archive when there is nothing to put in it", async () => {
    const bytes = await u8(zipFiles([]));
    expect(bytes.length).toBe(22);
    expect(new DataView(bytes.buffer, bytes.byteOffset).getUint32(0, true)).toBe(0x06054b50);
  });
});
