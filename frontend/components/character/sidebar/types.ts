import type { Catalog, Character } from "@/lib/types";

export type SidebarBlockProps = {
  catalog: Catalog;
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  t: (key: string, fallback?: string) => string;
  career: boolean;
  error?: string | null;
  patch?: (body: Record<string, unknown>) => void | Promise<void>;
};
