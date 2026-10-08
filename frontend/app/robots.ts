import type { MetadataRoute } from "next";
import { siteOrigin } from "@/lib/site";

/**
 * Until this existed the origin answered 404 for `/robots.txt` and Cloudflare
 * filled the gap with its managed one: a block of content-signal comments and
 * not a single `Allow`, `Disallow` or `Sitemap`. Crawling was permitted by
 * default, which is all it said. This says it on purpose, and names the
 * sitemap.
 *
 * `/share` stays crawlable so crawlers can read its `noindex` metadata.
 * Blocking it here would prevent that and could leave the URL in search results.
 *
 * `/api/` is disallowed because nothing under it is a document. The catalog
 * alone is 3 MB of JSON that no search result could ever want, and it is the
 * single most expensive thing this service can be asked for.
 */
export default async function robots(): Promise<MetadataRoute.Robots> {
  const origin = await siteOrigin();
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/api/"] }],
    sitemap: `${origin}/sitemap.xml`,
  };
}
