import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/site", () => ({ siteOrigin: async () => "https://chummer.example" }));

const load = async () => (await import("./sitemap")).default();

describe("sitemap", () => {
  it("lists the app and the manual, absolutely", async () => {
    const entries = await load();
    expect(entries.map((entry) => entry.url)).toEqual([
      "https://chummer.example/",
      // a file in `public/`, so nothing but this list knows it exists
      "https://chummer.example/manual/index.html",
    ]);
  });

  it("claims no lastModified", async () => {
    // `new Date()` here would tell every crawl the page had just changed
    for (const entry of await load()) expect(entry.lastModified).toBeUndefined();
  });

  it("does not list /share", async () => {
    for (const entry of await load()) expect(entry.url).not.toContain("/share");
  });
});
