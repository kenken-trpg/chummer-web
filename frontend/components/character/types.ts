import type { Catalog, Character } from "@/lib/types";

export type TabPanelProps = {
  catalog: Catalog;
  character: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  setCharacter: (next: Character) => void;
};
