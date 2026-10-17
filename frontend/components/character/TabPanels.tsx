"use client";
import dynamic from "next/dynamic";
import type { SheetLayout } from "@/components/CharacterSheet";
import type { TabPanelProps } from "@/components/character/types";
import { ChecklistPanel } from "@/components/character/ChecklistPanel";
import { AttrsTab } from "@/components/character/tabs/AttrsTab";
import { BioTab } from "@/components/character/tabs/BioTab";
import { ContactsTab } from "@/components/character/tabs/ContactsTab";
import { MetaTab } from "@/components/character/tabs/MetaTab";
import { PriorityTab } from "@/components/character/tabs/PriorityTab";
import { QualitiesTab } from "@/components/character/tabs/QualitiesTab";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import type { Tab } from "@/lib/character/constants";
import { useUiText } from "@/lib/i18n";
import { scopeTr, type TranslationKind } from "@/lib/ui-strings";

/**
 * Which tabs are in the first bundle and which arrive when they are opened.
 *
 * One tab is on screen at a time, so shipping all twenty-three to draw one is
 * most of the client bundle spent on panels the visitor may never open. The
 * split follows what a character creation actually touches:
 *
 * **Static** — the tabs of chargen itself. `priority` is what opens, and
 * metatype → attributes → skills → qualities is the path from there, with
 * contacts and bioware alongside. Fetching these on click would trade bytes
 * for a stall in the one sequence everybody walks.
 *
 * **Dynamic** — the heavy ones (`gear` is by far the largest tab in the tree,
 * `cyber` next) and everything behind `enabled_tabs`: the magic and resonance
 * panels do not exist for a mundane character at all, so a street samurai
 * downloading the spell list is pure waste. The character sheet goes with
 * them: it is a whole second renderer of the character, and it is a view
 * rather than a step.
 *
 * `ssr: false` on none of them — these are client components inside a client
 * page, and prerendering the panel that is open costs nothing extra.
 */
function TabLoading() {
  const { ui } = useUiText();
  return <p className="muted">{ui("app.loading")}</p>;
}

/** `next/dynamic` requires the options to be an object literal — a shared
 *  constant is rejected at build time — so `{ loading: TabLoading }` is
 *  repeated rather than named. */
const CharacterSheet = dynamic(() => import("@/components/CharacterSheet"), {
  loading: TabLoading,
});
const SheetDescEditor = dynamic(
  () => import("@/components/character/SheetDescEditor").then((m) => m.SheetDescEditor),
  { loading: TabLoading },
);
const AdeptTab = dynamic(
  () => import("@/components/character/tabs/AdeptTab").then((m) => m.AdeptTab),
  { loading: TabLoading },
);
const AIProgramsTab = dynamic(
  () => import("@/components/character/tabs/AIProgramsTab").then((m) => m.AIProgramsTab),
  { loading: TabLoading },
);
const ComplexFormsTab = dynamic(
  () => import("@/components/character/tabs/ComplexFormsTab").then((m) => m.ComplexFormsTab),
  { loading: TabLoading },
);
const CyberTab = dynamic(
  () => import("@/components/character/tabs/CyberTab").then((m) => m.CyberTab),
  { loading: TabLoading },
);
const FociTab = dynamic(
  () => import("@/components/character/tabs/FociTab").then((m) => m.FociTab),
  { loading: TabLoading },
);
const GearTab = dynamic(
  () => import("@/components/character/tabs/GearTab").then((m) => m.GearTab),
  { loading: TabLoading },
);
const InitiationTab = dynamic(
  () => import("@/components/character/tabs/InitiationTab").then((m) => m.InitiationTab),
  { loading: TabLoading },
);
const MartialTab = dynamic(
  () => import("@/components/character/tabs/MartialTab").then((m) => m.MartialTab),
  { loading: TabLoading },
);
const SpellsTab = dynamic(
  () => import("@/components/character/tabs/SpellsTab").then((m) => m.SpellsTab),
  { loading: TabLoading },
);
const SpiritsTab = dynamic(
  () => import("@/components/character/tabs/SpiritsTab").then((m) => m.SpiritsTab),
  { loading: TabLoading },
);
const SpritesTab = dynamic(
  () => import("@/components/character/tabs/SpritesTab").then((m) => m.SpritesTab),
  { loading: TabLoading },
);
const SubmersionTab = dynamic(
  () => import("@/components/character/tabs/SubmersionTab").then((m) => m.SubmersionTab),
  { loading: TabLoading },
);

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
      {tab === "aiprograms" && d.enabled_tabs.includes("advanced programs") && (
        <AIProgramsTab {...panel} />
      )}
    </>
  );
}
