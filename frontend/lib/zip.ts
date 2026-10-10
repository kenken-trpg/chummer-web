/**
 * A minimal ZIP writer: enough to put one file in an archive, and no more.
 *
 * Udonarium ships a character piece as a zip holding `data.xml`, and it reads
 * *only* that — handed a bare `.xml` it still runs the unzipper and fails with
 * "End of central directory not found". So the export has to produce a zip,
 * and the frontend has no runtime dependencies to produce one with.
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
 * A zip holding a single stored file.
 *
 * The name is written with the UTF-8 flag (bit 11) set, so a non-ASCII entry
 * name is read back as UTF-8 rather than as the archive's legacy code page.
 */
export function zipSingleFile(name: string, content: string, at: Date = new Date()): Blob {
  const data = new TextEncoder().encode(content);
  const nameBytes = new TextEncoder().encode(name);
  const { date, time } = dosDateTime(at);
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

  const central = new DataView(new ArrayBuffer(46));
  central.setUint32(0, 0x02014b50, true); // central directory header signature
  central.setUint16(4, 20, true); // version made by
  central.setUint16(6, 20, true); // version needed
  central.setUint16(8, 0x0800, true);
  central.setUint16(10, 0, true);
  central.setUint16(12, time, true);
  central.setUint16(14, date, true);
  central.setUint32(16, sum, true);
  central.setUint32(20, data.length, true);
  central.setUint32(24, data.length, true);
  central.setUint16(28, nameBytes.length, true);
  central.setUint16(30, 0, true); // extra
  central.setUint16(32, 0, true); // comment
  central.setUint16(34, 0, true); // disk number
  central.setUint16(36, 0, true); // internal attributes
  central.setUint32(38, 0, true); // external attributes
  central.setUint32(42, 0, true); // offset of the local header

  const centralSize = central.byteLength + nameBytes.length;
  const centralOffset = local.byteLength + nameBytes.length + data.length;

  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); // end of central directory signature
  end.setUint16(4, 0, true); // this disk
  end.setUint16(6, 0, true); // disk with the central directory
  end.setUint16(8, 1, true); // entries on this disk
  end.setUint16(10, 1, true); // entries in total
  end.setUint32(12, centralSize, true);
  end.setUint32(16, centralOffset, true);
  end.setUint16(20, 0, true); // comment length

  return new Blob([local, nameBytes, data, central, nameBytes, end], { type: "application/zip" });
}
