/**
 * A minimal ZIP writer: enough to put a few small files in an archive, and no
 * more.
 *
 * Udonarium ships a character piece as a zip holding `data.xml`. It has two
 * ways in and they do not agree: dropping a file on the table reads a bare
 * `.xml` fine, but the 「ZIP読込」 file input runs the unzipper over whatever it
 * is handed and fails a plain xml with "End of central directory not found" —
 * although its own `accept` list advertises `application/xml`. A zip works
 * either way, so that is what the export writes, and the frontend has no
 * runtime dependencies to write one with.
 *
 * Entries are stored, not deflated (method 0). A character is a few kilobytes
 * of XML; compressing it would save nothing anyone can notice and would mean
 * either pulling in a deflate implementation or depending on
 * `CompressionStream`, which this does not need to do.
 *
 * Only what one small file needs is implemented: no Zip64, no encryption, no
 * directory entries, no data descriptors.
 */

/** Reversed-polynomial CRC-32 (IEEE 802.3), the checksum a zip entry carries. */
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

export function crc32(bytes: Uint8Array): number {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

/** MS-DOS date and time, which is what a zip header stores. Seconds have
 *  two-second resolution there, and the epoch is 1980. */
function dosDateTime(at: Date): { date: number; time: number } {
  const year = Math.max(at.getFullYear() - 1980, 0);
  return {
    date: (year << 9) | ((at.getMonth() + 1) << 5) | at.getDate(),
    time: (at.getHours() << 11) | (at.getMinutes() << 5) | (at.getSeconds() >> 1),
  };
}

/**
 * A zip holding the given files, each stored.
 *
 * Names are written with the UTF-8 flag (bit 11) set, so a non-ASCII entry
 * name is read back as UTF-8 rather than as the archive's legacy code page.
 */
export function zipFiles(files: { name: string; content: string }[], at: Date = new Date()): Blob {
  const encoder = new TextEncoder();
  const { date, time } = dosDateTime(at);
  const parts: BlobPart[] = [];
  const central: BlobPart[] = [];
  let offset = 0;
  let centralSize = 0;

  for (const file of files) {
    const data = encoder.encode(file.content);
    const nameBytes = encoder.encode(file.name);
    const sum = crc32(data);

    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034b50, true); // local file header signature
    local.setUint16(4, 20, true); // version needed (2.0)
    local.setUint16(6, 0x0800, true); // flags: UTF-8 name
    local.setUint16(8, 0, true); // method: stored
    local.setUint16(10, time, true);
    local.setUint16(12, date, true);
    local.setUint32(14, sum, true);
    local.setUint32(18, data.length, true); // compressed size
    local.setUint32(22, data.length, true); // uncompressed size
    local.setUint16(26, nameBytes.length, true);
    local.setUint16(28, 0, true); // extra field length

    const entry = new DataView(new ArrayBuffer(46));
    entry.setUint32(0, 0x02014b50, true); // central directory header signature
    entry.setUint16(4, 20, true); // version made by
    entry.setUint16(6, 20, true); // version needed
    entry.setUint16(8, 0x0800, true);
    entry.setUint16(10, 0, true);
    entry.setUint16(12, time, true);
    entry.setUint16(14, date, true);
    entry.setUint32(16, sum, true);
    entry.setUint32(20, data.length, true);
    entry.setUint32(24, data.length, true);
    entry.setUint16(28, nameBytes.length, true);
    entry.setUint16(30, 0, true); // extra
    entry.setUint16(32, 0, true); // comment
    entry.setUint16(34, 0, true); // disk number
    entry.setUint16(36, 0, true); // internal attributes
    entry.setUint32(38, 0, true); // external attributes
    entry.setUint32(42, offset, true); // offset of this entry's local header

    parts.push(local, nameBytes, data);
    central.push(entry, nameBytes);
    offset += local.byteLength + nameBytes.length + data.length;
    centralSize += entry.byteLength + nameBytes.length;
  }

  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); // end of central directory signature
  end.setUint16(4, 0, true); // this disk
  end.setUint16(6, 0, true); // disk with the central directory
  end.setUint16(8, files.length, true); // entries on this disk
  end.setUint16(10, files.length, true); // entries in total
  end.setUint32(12, centralSize, true);
  end.setUint32(16, offset, true); // where the central directory starts
  end.setUint16(20, 0, true); // comment length

  return new Blob([...parts, ...central, end], { type: "application/zip" });
}

/** A zip holding one stored file. */
export function zipSingleFile(name: string, content: string, at: Date = new Date()): Blob {
  return zipFiles([{ name, content }], at);
}
