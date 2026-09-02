import type { Catalog, Character } from "@/lib/types";
import { textSheet } from "@/lib/character/text-sheet";
import { buildSheetData, type SheetLayout } from "@/lib/character/sheet-data";
import { SheetHeader } from "@/components/character/sheet/SheetHeader";
import { CoreSection } from "@/components/character/sheet/sections/Core";
import { SkillsSection } from "@/components/character/sheet/sections/Skills";
import { KnowledgeSection } from "@/components/character/sheet/sections/Knowledge";
import { CareerSection } from "@/components/character/sheet/sections/Career";
import { QualitiesSection } from "@/components/character/sheet/sections/Qualities";
import { ActionDpSection } from "@/components/character/sheet/sections/ActionDp";
import { CombatSection } from "@/components/character/sheet/sections/Combat";
import { WareSection } from "@/components/character/sheet/sections/Ware";
import { MatrixSection } from "@/components/character/sheet/sections/Matrix";
import { MagicSection } from "@/components/character/sheet/sections/Magic";
import { ResonanceSection } from "@/components/character/sheet/sections/Resonance";
import { MartialSection } from "@/components/character/sheet/sections/Martial";
import { ContactsSection } from "@/components/character/sheet/sections/Contacts";
import { VehiclesSection } from "@/components/character/sheet/sections/Vehicles";
import { DrugsSection } from "@/components/character/sheet/sections/Drugs";
import { SinSection } from "@/components/character/sheet/sections/Sin";
import { MiscGearSection } from "@/components/character/sheet/sections/MiscGear";
import { DescriptionSection } from "@/components/character/sheet/sections/Description";

export type { SheetLayout } from "@/lib/character/sheet-data";

export default function CharacterSheet({
  character,
  catalog,
  tr,
  layout = "standard",
}: {
  character: Character;
  catalog: Catalog;
  tr: (name: string) => string;
  layout?: SheetLayout;
}) {
  const s = buildSheetData({ character, catalog, tr, layout });

  if (layout === "text") {
    return (
      <pre className="sheet-text">
        {textSheet({
          character,
          d: s.d,
          tr,
          t: s.t,
          totals: s.totals,
          enabled: s.enabled,
          activeSkills: s.activeSkills,
          groups: s.groups,
          exotic: s.exotic,
          knowledge: s.knowledge,
          qualities: s.qualities,
          weapons: s.weapons,
          armors: s.armors,
          cyber: s.cyber,
          bio: s.bio,
          gearMisc: s.gearMisc,
          drugs: s.drugs,
          sins: s.sins,
        })}
      </pre>
    );
  }

  const variantClass =
    layout === "compact"
      ? " character-sheet--compact"
      : layout === "print"
        ? " character-sheet--print"
        : "";

  return (
    <article className={`character-sheet${variantClass}`}>
      <SheetHeader {...s} />
      <CoreSection {...s} />
      <SkillsSection {...s} />
      <KnowledgeSection {...s} />
      <CareerSection {...s} />
      <QualitiesSection {...s} />
      <ActionDpSection {...s} />
      <CombatSection {...s} />
      <WareSection {...s} />
      <MatrixSection {...s} />
      <MagicSection {...s} />
      <ResonanceSection {...s} />
      <MartialSection {...s} />
      <ContactsSection {...s} />
      <VehiclesSection {...s} />
      <DrugsSection {...s} />
      <SinSection {...s} />
      <MiscGearSection {...s} />
      <DescriptionSection {...s} />
      <footer className="sheet-footer">Chummer Web ・ 非公式 Shadowrun 5e ・ 卓用表示／印刷</footer>
    </article>
  );
}
