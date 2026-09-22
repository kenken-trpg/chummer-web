import CharacterSheet from "@/components/CharacterSheet";
import type { SheetLayout } from "@/components/CharacterSheet";
import type { TabPanelProps } from "@/components/character/types";
import { ChecklistPanel } from "@/components/character/ChecklistPanel";
import { SheetDescEditor } from "@/components/character/SheetDescEditor";
import { AdeptTab } from "@/components/character/tabs/AdeptTab";
import { AttrsTab } from "@/components/character/tabs/AttrsTab";
import { BioTab } from "@/components/character/tabs/BioTab";
import { ComplexFormsTab } from "@/components/character/tabs/ComplexFormsTab";
import { ContactsTab } from "@/components/character/tabs/ContactsTab";
import { CyberTab } from "@/components/character/tabs/CyberTab";
import { FociTab } from "@/components/character/tabs/FociTab";
import { GearTab } from "@/components/character/tabs/GearTab";
import { InitiationTab } from "@/components/character/tabs/InitiationTab";
import { MartialTab } from "@/components/character/tabs/MartialTab";
import { MetaTab } from "@/components/character/tabs/MetaTab";
import { PriorityTab } from "@/components/character/tabs/PriorityTab";
import { QualitiesTab } from "@/components/character/tabs/QualitiesTab";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import { SpellsTab } from "@/components/character/tabs/SpellsTab";
import { SpiritsTab } from "@/components/character/tabs/SpiritsTab";
import { SpritesTab } from "@/components/character/tabs/SpritesTab";
import { SubmersionTab } from "@/components/character/tabs/SubmersionTab";
import type { Tab } from "@/lib/character/constants";
import { scopeTr, type TranslationKind } from "@/lib/ui-strings";

/** The panel with `tr` narrowed to the kinds of thing a tab shows. */
function scoped(panel: TabPanelProps, ...kinds: TranslationKind[]): TabPanelProps {
  return { ...panel, tr: scopeTr(panel.tr, ...kinds) };
}

export function TabPanels({
  tab,
  panel,
  sheetLayout,
  onPortraitFile,
  setTab,
}: {
  tab: Tab;
  panel: TabPanelProps;
  sheetLayout: SheetLayout;
  onPortraitFile: (file: File) => void | Promise<void>;
  setTab: (t: Tab) => void;
}) {
  const { catalog, character: ch, d, tr, patch } = panel;
  return (
    <>
      {tab === "check" && <ChecklistPanel panel={panel} setTab={setTab} />}
      {tab === "sheet" && <SheetDescEditor ch={ch} patch={patch} onPortraitFile={onPortraitFile} />}
      {tab === "sheet" && (
        <CharacterSheet character={ch} catalog={catalog} tr={tr} layout={sheetLayout} />
      )}
      {tab === "priority" && <PriorityTab {...panel} />}
      {tab === "meta" && <MetaTab {...panel} />}
      {tab === "attrs" && <AttrsTab {...panel} />}
      {tab === "skills" && <SkillsTab {...panel} />}
      {tab === "qualities" && <QualitiesTab {...panel} />}
      {tab === "cyber" && <CyberTab {...scoped(panel, "cyberware")} />}
      {tab === "bio" && <BioTab {...panel} />}
      {tab === "gear" && <GearTab {...scoped(panel, "gear", "armor")} />}
      {tab === "contacts" && <ContactsTab {...panel} />}
      {tab === "martial" && <MartialTab {...panel} />}
      {tab === "initiation" && d.enabled_tabs.includes("initiation") && (
        <InitiationTab {...panel} />
      )}
      {tab === "submersion" && d.enabled_tabs.includes("submersion") && (
        <SubmersionTab {...panel} />
      )}
      {tab === "adept" && d.enabled_tabs.includes("adept") && (
        <AdeptTab {...scoped(panel, "power")} />
      )}
      {tab === "spells" && d.enabled_tabs.includes("spells") && <SpellsTab {...panel} />}
      {tab === "spirits" && d.enabled_tabs.includes("spirits") && (
        <SpiritsTab {...scoped(panel, "critter_power")} />
      )}
      {tab === "foci" && d.enabled_tabs.includes("foci") && <FociTab {...panel} />}
      {tab === "complexforms" && d.enabled_tabs.includes("complexforms") && (
        <ComplexFormsTab {...panel} />
      )}
      {tab === "sprites" && d.enabled_tabs.includes("sprites") && <SpritesTab {...panel} />}
    </>
  );
}
