import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/site", () => ({ siteOrigin: async () => "https://chummer.example" }));

const load = async () => (await import("./sitemap")).default();

describe("sitemap", () => {
  it("lists the one page there is, absolutely", async () => {
    const entries = await load();
    expect(entries).toHaveLength(1);
    expect(entries[0]!.url).toBe("https://chummer.example/");
  });

  it("claims no lastModified", async () => {
    // `new Date()` here would tell every crawl the page had just changed
    expect((await load())[0]!.lastModified).toBeUndefined();
  });

  it("does not list /share", async () => {
    for (const entry of await load()) expect(entry.url).not.toContain("/share");
  });
});
