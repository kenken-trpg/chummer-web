import { headers } from "next/headers";

const LOOPBACK = /^(localhost|127\.\d+\.\d+\.\d+|\[::1\]|[a-z0-9-]+\.localhost)$/i;

function httpOrigin(value: string): string | undefined {
  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) return;
    return url.origin;
  } catch {
    return;
  }
}

function hostOrigin(value: string): string | undefined {
  // Reject paths, credentials, schemes and whitespace before URL parsing.
  if (!/^[a-z0-9.\[\]:-]+$/i.test(value)) return;
  const origin = httpOrigin(`https://${value}`);
  if (!origin) return;
  return LOOPBACK.test(new URL(origin).hostname) ? httpOrigin(`http://${value}`) : origin;
}

/**
 * The origin to print inside a document that has to name itself: `robots.txt`'s
 * `Sitemap:` line, `sitemap.xml`'s `<loc>`, and the canonical link in the page
 * head. All three have to be absolute, and none of them can be known at build
 * time — this app is self-hostable, and the same image answers on
 * `localhost:3000`, on a Cloud Run URL and on whatever hostname a reader
 * actually typed.
 *
 * So it is read per request, from the same places and in the same order as the
 * CSP's `Reporting-Endpoints`: `PUBLIC_ORIGIN` if the
 * operator set it, then the proxy's `x-forwarded-host`, then this request's own
 * `Host`. Reading `headers()` is also what keeps `robots.txt` and `sitemap.xml`
 * out of the static prerender they would otherwise get, which is the point —
 * a build-time origin would be wrong for every deployment but one.
 *
 * `x-forwarded-proto` is deliberately not consulted, like the CSP origin.
 * The host fallback assumes https for anything that is not a
 * loopback name, because a bare hostname reaching this process means something
 * in front terminated TLS.
 */
export async function siteOrigin(): Promise<string> {
  const h = await headers();
  return (
    httpOrigin(process.env.PUBLIC_ORIGIN ?? "") ??
    hostOrigin((h.get("x-forwarded-host") ?? "").split(",")[0]!.trim()) ??
    hostOrigin((h.get("host") ?? "").trim()) ??
    "http://localhost:3000"
  );
}
