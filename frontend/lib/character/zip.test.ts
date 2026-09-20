import { describe, expect, it } from "vitest";
import { unzip, ZipError } from "@/lib/character/zip";
import { makeZip as zip } from "@/tests/zip-fixture";

const text = (bytes: Uint8Array) => new TextDecoder().decode(bytes);

describe("unzip", () => {
  it("reads deflated and stored members back", async () => {
    const entries = await unzip(
      await zip([
        { name: "style/settings/nt.xml", data: "<settings><name>NT</name></settings>" },
        { name: "style/customdata/pack/manifest.xml", data: "<manifest/>", stored: true },
      ]),
    );
    expect(entries.map((e) => e.path)).toEqual([
      "style/settings/nt.xml",
      "style/customdata/pack/manifest.xml",
    ]);
    expect(text(entries[0].bytes)).toBe("<settings><name>NT</name></settings>");
    expect(text(entries[1].bytes)).toBe("<manifest/>");
  });

  it("leaves out directory entries and the housekeeping files", async () => {
    // They would otherwise land in the content hash the merged dataset is
    // keyed by, so the same pack from a Mac and from Windows would be two
    // different datasets.
    const entries = await unzip(
      await zip([
        { name: "style/", data: "" },
        { name: "style/customdata/", data: "" },
        { name: "__MACOSX/style/._manifest.xml", data: "junk" },
        { name: "style/customdata/.DS_Store", data: "junk" },
        { name: "style/customdata/pack/manifest.xml", data: "<manifest/>" },
      ]),
    );
    expect(entries.map((e) => e.path)).toEqual(["style/customdata/pack/manifest.xml"]);
  });

  // Windows Explorer on a Japanese system writes the OEM code page and leaves
  // the UTF-8 flag clear — and a ruleset written in Japanese has Japanese
  // directory names, so this is the ordinary case for this app, not an exotic
  // one. Without the fallback the whole pack lands under a mojibake path and
  // the settings file's `<customdatadirectoryname>` matches nothing.
  it("falls back to Shift_JIS for a name that is not UTF-8", async () => {
    // 新東京/manifest.xml in cp932
    const name = new Uint8Array([
      0x90, 0x56, 0x93, 0x8c, 0x8b, 0x9e, 0x2f, 0x6d, 0x61, 0x6e, 0x69, 0x66, 0x65, 0x73, 0x74,
      0x2e, 0x78, 0x6d, 0x6c,
    ]);
    const entries = await unzip(await zip([{ name, data: "<manifest/>" }], { utf8: false }));
    expect(entries[0].path).toBe("新東京/manifest.xml");
  });

  it("says a file is not a zip rather than reading nonsense out of it", async () => {
    const data = new TextEncoder().encode("<settings>this is the xml, not the archive</settings>");
    await expect(unzip(data.buffer as ArrayBuffer)).rejects.toThrow(ZipError);
    await expect(unzip(new ArrayBuffer(4))).rejects.toMatchObject({ reason: "not-a-zip" });
  });

  it("refuses a member it cannot decompress instead of merging part of a pack", async () => {
    const archive = new Uint8Array(await zip([{ name: "a.xml", data: "<a/>" }]));
    // bzip2 (12) in both headers — a pack half-applied is worse than one that
    // said it could not be opened
    new DataView(archive.buffer).setUint16(8, 12, true);
    const dirAt = archive.byteLength - 22 - 46 - "a.xml".length;
    new DataView(archive.buffer).setUint16(dirAt + 10, 12, true);
    await expect(unzip(archive.buffer as ArrayBuffer)).rejects.toMatchObject({
      reason: "unsupported",
    });
  });
});
