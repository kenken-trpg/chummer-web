import type { MetadataRoute } from "next";
import { siteOrigin } from "@/lib/site";

/**
 * One entry, because there is one page. Everything a reader does here happens
 * on `/` — the tabs are state, not routes — and `/share` is deliberately kept
 * out of the index by its layout's noindex metadata.
 *
 * No `lastModified`. The honest value is the date this app was last deployed,
 * which nothing in a running container knows, and the easy value — `new Date()`
 * — would claim the page changed on every crawl. A crawler that learns the
 * field is noise stops reading it; one that believes it is told the page is
 * always new. Leaving it out says nothing, which is true.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const origin = await siteOrigin();
  return [{ url: `${origin}/`, changeFrequency: "weekly", priority: 1 }];
}
