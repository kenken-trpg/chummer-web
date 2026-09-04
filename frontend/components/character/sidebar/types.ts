import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";

export type SidebarBlockProps = {
  catalog: Catalog;
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  t: (key: string, fallback?: string) => string;
  /** App copy. Passed down rather than hooked in each block so the whole
   *  sidebar re-renders from one `useUiText()`; `t`/`tr` above are the *game
   *  term* translators, which is a different layer (docs/i18n.md). */
  ui: UiFn;
  career: boolean;
  error?: string | null;
  patch?: (body: Record<string, unknown>) => void | Promise<void>;
};
