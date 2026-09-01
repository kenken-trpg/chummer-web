import type { Metadata } from "next";
import { IBM_Plex_Sans_JP } from "next/font/google";
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja" className={plexSansJp.variable}>
      <body>{children}</body>
    </html>
  );
}
