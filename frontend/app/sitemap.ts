import type { MetadataRoute } from "next";
import { siteOrigin } from "@/lib/site";

/**
 * Two entries: the app and the manual. Everything a reader does in the app
 * happens on `/` — the tabs are state, not routes — and `/share` is
 * deliberately kept out of the index by its layout's noindex metadata.
 * The manual is a static page under `public/`, which Next knows nothing about,
 * so it has to be named here by hand — by the URL it settles on, not the
 * `/manual` shorthand that redirects to it.
 *
 * No `lastModified`. The honest value is the date this app was last deployed,
 * which nothing in a running container knows, and the easy value — `new Date()`
 * — would claim the page changed on every crawl. A crawler that learns the
 * field is noise stops reading it; one that believes it is told the page is
 * always new. Leaving it out says nothing, which is true.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const origin = await siteOrigin();
  return [
    { url: `${origin}/`, changeFrequency: "weekly", priority: 1 },
    { url: `${origin}/manual/index.html`, changeFrequency: "monthly", priority: 0.5 },
  ];
}
