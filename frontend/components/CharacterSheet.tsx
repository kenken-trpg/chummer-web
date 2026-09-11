import type { Catalog, Character } from "@/lib/types";
import { useUiText } from "@/lib/i18n";
import { textSheet } from "@/lib/character/text-sheet";
import { buildSheetData, type SheetLayout } from "@/lib/character/sheet-data";
import { useWareCompact } from "@/lib/character/useWareCompact";
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
import { PrintStatBlock } from "@/components/character/sheet/sections/print/PrintStatBlock";
import { PrintConditionMonitor } from "@/components/character/sheet/sections/print/PrintConditionMonitor";

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
  const { ui, locale } = useUiText();
  const [wareNamesOnly, setWareNamesOnly] = useWareCompact("sheetWareNames");
  const s = buildSheetData({ character, catalog, tr, layout, locale, wareNamesOnly });
  // Compact lists ware by name already; the other three get the choice. The
  // switch itself never prints.
  const wareSwitch =
    layout === "compact" ? null : (
      <label className="option-row no-print">
        <input
          type="checkbox"
          checked={wareNamesOnly}
          onChange={(e) => setWareNamesOnly(e.target.checked)}
        />
        {ui("sheet.wareNamesOnly")}
      </label>
    );

  if (layout === "text") {
    return (
      <>
        {wareSwitch}
        <pre className="sheet-text">
          {textSheet({
            character,
            d: s.d,
            tr,
            t: s.t,
            ui: s.ui,
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
            wareNamesOnly: s.wareNamesOnly,
          })}
        </pre>
      </>
    );
  }

  const footer = <footer className="sheet-footer">{ui("sheet.footer")}</footer>;

  if (layout === "print") {
    return (
      <article className="character-sheet character-sheet--print">
        {wareSwitch}
        <SheetHeader {...s} />
        <PrintStatBlock {...s} />
        <PrintConditionMonitor {...s} />
        <SkillsSection {...s} />
        <KnowledgeSection {...s} />
        <CareerSection {...s} />
        <ActionDpSection {...s} />
        <QualitiesSection {...s} />
        <div className="print-page-2">
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
        </div>
        {footer}
      </article>
    );
  }

  return (
    <article
      className={`character-sheet${layout === "compact" ? " character-sheet--compact" : ""}`}
    >
      {wareSwitch}
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
      {footer}
    </article>
  );
}
