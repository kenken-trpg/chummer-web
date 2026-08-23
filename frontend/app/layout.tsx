import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chummer Web",
  description: "非公式 Shadowrun 5e キャラクター作成",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
