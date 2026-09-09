import { describe, expect, it } from "vitest";
import { readStyleFolder } from "@/lib/character/customdata-store";

/** A `File` that reports a directory path, the way a folder pick does. */
function entry(path: string, text: string): File {
  const file = new File([text], path.split("/").pop() as string, { type: "text/xml" });
  Object.defineProperty(file, "webkitRelativePath", { value: path });
  return file;
}

const list = (...files: File[]) => files as unknown as FileList;

describe("readStyleFolder", () => {
  it("drops the picked folder's own name, keeping what a settings file names", async () => {
    // the user picks `customdata`, and the settings file refers to the
    // directories inside it
    const { customdata: files } = await readStyleFolder(
      list(entry("customdata/NTS4C08/manifest.xml", "<manifest/>")),
    );
    expect(Object.keys(files)).toEqual(["NTS4C08/manifest.xml"]);
  });

  it("leaves non-XML files out", async () => {
    // Chummer ignores them too, and they would change the content hash for
    // no reason
    const { customdata: files } = await readStyleFolder(
      list(
        entry("customdata/d/custom_gear.xml", "<chummer/>"),
        entry("customdata/d/readme.txt", "hello"),
        entry("customdata/.DS_Store", "junk"),
      ),
    );
    expect(Object.keys(files)).toEqual(["d/custom_gear.xml"]);
  });

  it("reads the text of each file", async () => {
    const { customdata: files } = await readStyleFolder(
      list(entry("cd/d/custom_x.xml", "<chummer>hi</chummer>")),
    );
    expect(files["d/custom_x.xml"]).toBe("<chummer>hi</chummer>");
  });

  it("keeps a bare file name when the browser reports no path", async () => {
    const bare = new File(["<chummer/>"], "custom_x.xml", { type: "text/xml" });
    expect(Object.keys((await readStyleFolder(list(bare))).customdata)).toEqual(["custom_x.xml"]);
  });

  it("splits a whole ruleset folder into its settings and its custom data", async () => {
    // what a published ruleset actually looks like: the two halves as siblings
    const pick = await readStyleFolder(
      list(
        entry("スタイル/settings/b.xml", "<settings><name>B</name></settings>"),
        entry("スタイル/settings/a.xml", "<settings><name>A</name></settings>"),
        entry("スタイル/customdata/NTS/custom_gear.xml", "<chummer/>"),
      ),
    );
    expect(pick.settings.map((f) => f.name)).toEqual(["a.xml", "b.xml"]);
    expect(Object.keys(pick.customdata)).toEqual(["NTS/custom_gear.xml"]);
  });

  it("leaves the rest of the tree out of the dataset", async () => {
    // `sheets/` and anything else beside the two halves would change the
    // content hash without changing a single rule
    const pick = await readStyleFolder(
      list(
        entry("スタイル/customdata/NTS/custom_gear.xml", "<chummer/>"),
        entry("スタイル/sheets/ja-jp/sheet.xml", "<xsl/>"),
        entry("スタイル/notes.xml", "<x/>"),
      ),
    );
    expect(Object.keys(pick.customdata)).toEqual(["NTS/custom_gear.xml"]);
    expect(pick.settings).toEqual([]);
  });

  it("finds the settings half of a folder that has no custom data", async () => {
    const pick = await readStyleFolder(list(entry("スタイル/settings/a.xml", "<settings/>")));
    expect(pick.settings.map((f) => f.name)).toEqual(["a.xml"]);
    expect(pick.customdata).toEqual({});
  });

  it("reports no settings for a bare customdata pick", async () => {
    const pick = await readStyleFolder(list(entry("customdata/NTS/manifest.xml", "<manifest/>")));
    expect(pick.settings).toEqual([]);
    expect(Object.keys(pick.customdata)).toEqual(["NTS/manifest.xml"]);
  });
});
