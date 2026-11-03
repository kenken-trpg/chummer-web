import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { projectVersion, releaseUrl } from "@/lib/app-version";

describe("projectVersion", () => {
  it("reads the version the release check holds to the tag", () => {
    const text = readFileSync(resolve(__dirname, "../../backend/pyproject.toml"), "utf8");
    expect(projectVersion(text)).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("takes only [project]'s version", () => {
    const text = [
      "[tool.something]",
      'version = "9.9.9"',
      "[project]",
      'name = "x"',
      'version_scheme = "nope"',
      'version = "1.2.3"',
    ].join("\n");
    expect(projectVersion(text)).toBe("1.2.3");
  });

  it("is undefined without one", () => {
    expect(projectVersion('[project]\nname = "x"\n')).toBeUndefined();
    expect(projectVersion("")).toBeUndefined();
  });
});

describe("releaseUrl", () => {
  it("points at the tag's release", () => {
    expect(releaseUrl("https://github.com/o/r", "0.5.19")).toBe(
      "https://github.com/o/r/releases/tag/v0.5.19",
    );
  });
});
