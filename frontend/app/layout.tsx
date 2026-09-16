import type { Metadata } from "next";
import { IBM_Plex_Sans_JP } from "next/font/google";
import { connection } from "next/server";
import "./globals.css";

const plexSansJp = IBM_Plex_Sans_JP({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-plex-sans-jp",
  preload: false,
});

export const metadata: Metadata = {
  title: "Chummer Web",
  description: "非公式 Shadowrun 5e キャラクター作成",
};

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
