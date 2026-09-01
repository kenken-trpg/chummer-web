"use client";

import { useRef, useState } from "react";
import { CharacterSidebar } from "@/components/character/CharacterSidebar";
import { TabBar } from "@/components/character/TabBar";
import { TabPanels } from "@/components/character/TabPanels";
import type { TabPanelProps } from "@/components/character/types";
import { Toolbar } from "@/components/character/Toolbar";
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

          <TabBar tab={tab} setTab={setTab} enabledTabs={d.enabled_tabs} />
        </div>

        <TabPanels
          tab={tab}
          panel={panel}
          sheetLayout={sheetLayout}
          onPortraitFile={onPortraitFile}
        />
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
