import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/site", () => ({ siteOrigin: async () => "https://chummer.example" }));

const load = async () => (await import("./robots")).default();

describe("robots", () => {
  it("names the sitemap absolutely", async () => {
    expect((await load()).sitemap).toBe("https://chummer.example/sitemap.xml");
  });

  it("allows /share to be crawled so its noindex metadata can be read", async () => {
    const [rule] = [(await load()).rules].flat();
    expect(rule!.disallow).toEqual(["/api/"]);
  });

  it("keeps crawlers out of /api, which serves no documents", async () => {
    const [rule] = [(await load()).rules].flat();
    expect(rule!.disallow).toContain("/api/");
  });

  it("allows the page itself", async () => {
    const [rule] = [(await load()).rules].flat();
    expect(rule!.allow).toBe("/");
    expect(rule!.userAgent).toBe("*");
  });
});
