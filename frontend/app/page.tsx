"use client";

import { useRef, useState } from "react";
import CharacterSheet from "@/components/CharacterSheet";
import { CharacterSidebar } from "@/components/character/CharacterSidebar";
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
import type { TabPanelProps } from "@/components/character/types";
import { Toolbar } from "@/components/character/Toolbar";
import { SheetDescEditor } from "@/components/character/SheetDescEditor";
import type { Tab } from "@/lib/character/constants";
import { useCharacterEditor } from "@/lib/character/useCharacterEditor";
import { useSheetLayout } from "@/lib/character/useSheetLayout";
import { useKeyboardShortcuts } from "@/lib/character/useKeyboardShortcuts";

export default function Page() {
  const [tab, setTab] = useState<Tab>("priority");
  const [sheetLayout, setSheetLayout] = useSheetLayout();
  const fileRef = useRef<HTMLInputElement>(null);
  const ed = useCharacterEditor({ onCharacterOpened: () => setTab("priority") });
  const { catalog, ch, error, tr, t, patch, setCh, undo, redo, onPortraitFile } = ed;
  useKeyboardShortcuts(undo, redo);

  if (error && !ch) {
    return (
      <div className="main">
        <p className="errors">{error}</p>
      </div>
    );
  }
  if (!catalog || !ch) {
    return <div className="main">読み込み中…</div>;
  }

  const d = ch.derived;
  const panel: TabPanelProps = {
    catalog,
    character: ch,
    d,
    tr,
    t,
    patch,
    setCharacter: (next) => setCh(next),
  };

  return (
    <div className={`app ${tab === "sheet" ? "sheet-mode" : ""}`}>
      <div className="main">
        <div className="no-print">
          <h1>CHUMMER WEB</h1>
          <p className="sub">
            非公式 Shadowrun 5e キャラクター作成。Catalyst / Topps 非提携。データは Chummer5a
            (GPL-3.0)。
          </p>

          <Toolbar
            ed={ed}
            ch={ch}
            catalog={catalog}
            tab={tab}
            setTab={setTab}
            sheetLayout={sheetLayout}
            setSheetLayout={setSheetLayout}
            fileRef={fileRef}
          />

          <div className="tabs">
            {(
              [
                ["priority", "優先度"],
                ["meta", "メタ"],
                ["attrs", "能力値"],
                ["skills", "技能"],
                ["qualities", "資質"],
                ["cyber", "サイバー"],
                ["bio", "バイオ"],
                ["gear", "ギア"],
                ["contacts", "コンタクト"],
                ["martial", "武道"],
                ...(d.enabled_tabs.includes("initiation")
                  ? [["initiation", "イニシエーション"] as const]
                  : []),
                ...(d.enabled_tabs.includes("submersion")
                  ? [["submersion", "サブマージョン"] as const]
                  : []),
                ...(d.enabled_tabs.includes("adept") ? [["adept", "アデプト"] as const] : []),
                ...(d.enabled_tabs.includes("spells") ? [["spells", "術式"] as const] : []),
                ...(d.enabled_tabs.includes("spirits") ? [["spirits", "精霊"] as const] : []),
                ...(d.enabled_tabs.includes("foci") ? [["foci", "フォーカス"] as const] : []),
                ...(d.enabled_tabs.includes("complexforms")
                  ? [["complexforms", "複合体"] as const]
                  : []),
                ...(d.enabled_tabs.includes("sprites") ? [["sprites", "スプライト"] as const] : []),
                ["sheet", "シート"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                className={`tab ${tab === k ? "active" : ""}`}
                onClick={() => setTab(k)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {tab === "sheet" && (
          <SheetDescEditor ch={ch} patch={patch} onPortraitFile={onPortraitFile} />
        )}
        {tab === "sheet" && (
          <CharacterSheet character={ch} catalog={catalog} tr={tr} layout={sheetLayout} />
        )}
        {tab === "priority" && <PriorityTab {...panel} />}
        {tab === "meta" && <MetaTab {...panel} />}
        {tab === "attrs" && <AttrsTab {...panel} />}
        {tab === "skills" && <SkillsTab {...panel} />}
        {tab === "qualities" && <QualitiesTab {...panel} />}
        {tab === "cyber" && <CyberTab {...panel} />}
        {tab === "bio" && <BioTab {...panel} />}
        {tab === "gear" && <GearTab {...panel} />}
        {tab === "contacts" && <ContactsTab {...panel} />}
        {tab === "martial" && <MartialTab {...panel} />}
        {tab === "initiation" && d.enabled_tabs.includes("initiation") && (
          <InitiationTab {...panel} />
        )}
        {tab === "submersion" && d.enabled_tabs.includes("submersion") && (
          <SubmersionTab {...panel} />
        )}
        {tab === "adept" && d.enabled_tabs.includes("adept") && <AdeptTab {...panel} />}
        {tab === "spells" && d.enabled_tabs.includes("spells") && <SpellsTab {...panel} />}
        {tab === "spirits" && d.enabled_tabs.includes("spirits") && <SpiritsTab {...panel} />}
        {tab === "foci" && d.enabled_tabs.includes("foci") && <FociTab {...panel} />}
        {tab === "complexforms" && d.enabled_tabs.includes("complexforms") && (
          <ComplexFormsTab {...panel} />
        )}
        {tab === "sprites" && d.enabled_tabs.includes("sprites") && <SpritesTab {...panel} />}
      </div>

      <CharacterSidebar
        catalog={catalog}
        character={ch}
        d={d}
        tr={tr}
        error={error}
        patch={patch}
      />
    </div>
  );
}
