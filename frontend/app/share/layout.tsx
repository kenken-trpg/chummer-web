import type { Metadata } from "next";

/**
 * A share URL *is* the character — the whole state rides in the fragment. Keep
 * crawlers out so a link pasted on a public page cannot put someone's build
 * into a search index. (The fragment never reaches our server, but a crawler
 * that follows the link would still archive the URL itself.)
 */
export const metadata: Metadata = {
  title: "共有ビュー | Chummer Web",
  robots: { index: false, follow: false, nocache: true },
};

export default function ShareLayout({ children }: { children: React.ReactNode }) {
  return children;
}
