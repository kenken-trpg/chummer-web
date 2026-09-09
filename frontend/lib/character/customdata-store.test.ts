import { describe, expect, it } from "vitest";
import { readCustomDataFolder } from "@/lib/character/customdata-store";

/** A `File` that reports a directory path, the way a folder pick does. */
function entry(path: string, text: string): File {
  const file = new File([text], path.split("/").pop() as string, { type: "text/xml" });
  Object.defineProperty(file, "webkitRelativePath", { value: path });
  return file;
}

const list = (...files: File[]) => files as unknown as FileList;

describe("readCustomDataFolder", () => {
  it("drops the picked folder's own name, keeping what a settings file names", async () => {
    // the user picks `customdata`, and the settings file refers to the
    // directories inside it
    const files = await readCustomDataFolder(
      list(entry("customdata/NTS4C08/manifest.xml", "<manifest/>")),
    );
    expect(Object.keys(files)).toEqual(["NTS4C08/manifest.xml"]);
  });

  it("leaves non-XML files out", async () => {
    // Chummer ignores them too, and they would change the content hash for
    // no reason
    const files = await readCustomDataFolder(
      list(
        entry("customdata/d/custom_gear.xml", "<chummer/>"),
        entry("customdata/d/readme.txt", "hello"),
        entry("customdata/.DS_Store", "junk"),
      ),
    );
    expect(Object.keys(files)).toEqual(["d/custom_gear.xml"]);
  });

  it("reads the text of each file", async () => {
    const files = await readCustomDataFolder(
      list(entry("cd/d/custom_x.xml", "<chummer>hi</chummer>")),
    );
    expect(files["d/custom_x.xml"]).toBe("<chummer>hi</chummer>");
  });

  it("keeps a bare file name when the browser reports no path", async () => {
    const bare = new File(["<chummer/>"], "custom_x.xml", { type: "text/xml" });
    expect(Object.keys(await readCustomDataFolder(list(bare)))).toEqual(["custom_x.xml"]);
  });
});
