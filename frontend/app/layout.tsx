import type { Metadata } from "next";
import { IBM_Plex_Sans_JP } from "next/font/google";
import { connection } from "next/server";
import { translate } from "@/lib/i18n/messages";
import { siteOrigin } from "@/lib/site";
import "./globals.css";

const plexSansJp = IBM_Plex_Sans_JP({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-plex-sans-jp",
  preload: false,
});

// A function rather than a constant, for `metadataBase`: the canonical link has
// to be absolute, and the origin is only knowable per request (see `siteOrigin`).
export async function generateMetadata(): Promise<Metadata> {
  return {
    metadataBase: new URL(await siteOrigin()),
    title: "Chummer Web",
    // Metadata is rendered on the server, before the reader's locale (kept in
    // localStorage) is known — so it is the reference locale, like `lang="ja"`.
    description: translate("ja", "app.meta.description"),
    // Drop query strings from the canonical. PUBLIC_ORIGIN also unifies aliases;
    // without it each request host gets its own canonical.
    alternates: { canonical: "/" },
  };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Render per request, never at build time. The CSP nonce (see `proxy.ts`) is
  // minted per request and Next stamps it on its script tags while rendering;
  // a page prerendered at build time has no request to read it from, ships
  // without it, and every one of its scripts is then blocked.
  await connection();
  return (
    <html lang="ja" className={plexSansJp.variable}>
      <body>{children}</body>
    </html>
  );
}
