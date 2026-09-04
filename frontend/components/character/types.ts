import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";

export type TabPanelProps = {
  catalog: Catalog;
  character: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  t: (key: string, fallback?: string) => string;
  /** App copy. `tr` / `t` above translate *game terms* from the catalog; this
   *  is the app's own wording, which lives in `lib/i18n` (docs/i18n.md).
   *  Passed down rather than hooked per tab, like `tr`. */
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  setCharacter: (next: Character) => void;
};
