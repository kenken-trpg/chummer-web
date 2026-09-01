"use client";

import type { Catalog, Character } from "@/lib/types";
import { makeT } from "@/lib/ui-strings";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { SidebarStatus } from "@/components/character/sidebar/SidebarStatus";
import { SidebarCareerEdit } from "@/components/character/sidebar/SidebarCareerEdit";
import { SidebarMagicStats } from "@/components/character/sidebar/SidebarMagicStats";
import { SidebarFlags } from "@/components/character/sidebar/SidebarFlags";
import { SidebarEconomy } from "@/components/character/sidebar/SidebarEconomy";
import { SidebarCareerRewards } from "@/components/character/sidebar/SidebarCareerRewards";
import { SidebarBudgets } from "@/components/character/sidebar/SidebarBudgets";
import { SidebarAwakened } from "@/components/character/sidebar/SidebarAwakened";
import { SidebarAttributes } from "@/components/character/sidebar/SidebarAttributes";

export function CharacterSidebar({
  catalog,
  character: ch,
  d,
  tr,
  error,
  patch,
}: {
  catalog: Catalog;
  character: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  error?: string | null;
  patch?: (body: Record<string, unknown>) => void | Promise<void>;
}) {
  const t = makeT(catalog);
  const career = Boolean(ch.career || d.career);

  const blockProps: SidebarBlockProps = { catalog, ch, d, tr, t, career, error, patch };
  return (
    <aside className="side no-print">
      <SidebarStatus {...blockProps} />
      <SidebarCareerEdit {...blockProps} />
      <SidebarMagicStats {...blockProps} />
      <SidebarFlags {...blockProps} />
      <SidebarEconomy {...blockProps} />
      <SidebarCareerRewards {...blockProps} />
      <SidebarBudgets {...blockProps} />
      <SidebarAwakened {...blockProps} />
      <SidebarAttributes {...blockProps} />
    </aside>
  );
}
