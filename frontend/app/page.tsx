"use client";

import { useRef, useState } from "react";
import { CharacterSidebar } from "@/components/character/CharacterSidebar";
import { shownTabs, TabBar } from "@/components/character/TabBar";
import { SheetSearch } from "@/components/character/SheetSearch";
import type { SheetSearchRequest } from "@/lib/character/sheet-search";
import { useSheetSearchNavigation } from "@/lib/character/useSheetSearchNavigation";
import { TabPanels } from "@/components/character/TabPanels";
import type { TabPanelProps } from "@/components/character/types";
import { Toolbar } from "@/components/character/Toolbar";
import { AppFooter } from "@/components/character/AppFooter";
import { LocaleSwitch } from "@/components/LocaleSwitch";
import type { Tab } from "@/lib/character/constants";
import { useCharacterEditor } from "@/lib/character/useCharacterEditor";
import { useSheetLayout } from "@/lib/character/useSheetLayout";
import { useKeyboardShortcuts } from "@/lib/character/useKeyboardShortcuts";
import { BooksProvider } from "@/lib/character/books";
import { useUiText } from "@/lib/i18n";
import { ExportReview } from "@/components/character/ExportReview";
import { CharacterRoster } from "@/components/character/CharacterRoster";
import { BackupReminder } from "@/components/character/BackupReminder";
import { SavedHistory } from "@/components/character/SavedHistory";
import { BulkImportReview } from "@/components/character/BulkImportReview";
import { ImportReport } from "@/components/character/ImportReport";
import { SheetUrlImport } from "@/components/character/SheetUrlImport";
import { GearReview } from "@/components/character/GearReview";

export default function Page() {
  const [tab, setTab] = useState<Tab>("priority");
  const [searchRequest, setSearchRequest] = useState<SheetSearchRequest | null>(null);
  const searchSerial = useRef(0);
  const changeTab = (next: Tab) => {
    setSearchRequest(null);
    setTab(next);
  };
  const [sheetLayout, setSheetLayout] = useSheetLayout();
  const fileRef = useRef<HTMLInputElement>(null);
  const ed = useCharacterEditor({ onCharacterOpened: () => changeTab("priority") });
  const { catalog, ch, error, notice, tr, trGroup, t, patch, setCh, undo, redo, onPortraitFile } =
    ed;
  const { ui } = useUiText();
  useKeyboardShortcuts(undo, redo);
  useSheetSearchNavigation(searchRequest, tab, ch?.id, () =>
    ed.setNotice(ui("app.sheetSearch.missing")),
  );

  if (error && !ch) {
    return (
      <div className="main">
        <p className="errors" role="alert">
          {error}
        </p>
      </div>
    );
  }
  if (!catalog || !ch) {
    return <div className="main">{ui("app.loading")}</div>;
  }

  const d = ch.derived;
  const panel: TabPanelProps = {
    catalog,
    searchRequest:
      searchRequest?.characterId === ch.id && searchRequest.target.tab === tab
        ? searchRequest
        : undefined,
    character: ch,
    d,
    tr,
    trGroup,
    t,
    ui,
    patch,
    setCharacter: (next) => setCh(next),
  };

  return (
    // The settings' book list narrows every catalog pick list, so it wraps the
    // whole editor rather than being threaded through `TabPanelProps`.
    <BooksProvider books={ch.settings?.books}>
      <div className={`app ${tab === "sheet" ? "sheet-mode" : ""}`}>
        {/* the toolbar is ~15 controls deep; give the keyboard a way past it */}
        <a className="skip-link" href="#main">
          {ui("nav.skipToMain")}
        </a>
        <main className="main" id="main">
          <header className="no-print">
            <div className="topline">
              <h1>CHUMMER WEB</h1>
              <LocaleSwitch />
            </div>
            <p className="sub">{ui("app.tagline")}</p>

            <Toolbar
              ed={ed}
              ch={ch}
              catalog={catalog}
              tab={tab}
              setTab={changeTab}
              sheetLayout={sheetLayout}
              setSheetLayout={setSheetLayout}
              fileRef={fileRef}
            />

            <SheetSearch
              key={ch.id}
              ed={ed}
              onNavigate={(target) => {
                setSearchRequest({ target, characterId: ch.id, serial: ++searchSerial.current });
                setTab(target.tab);
              }}
            />
            <CharacterRoster ed={ed} />
            <BackupReminder ed={ed} />
            <SavedHistory ed={ed} />
            <SheetUrlImport ed={ed} />
            <div role="status">{notice ? <p className="notice">{notice}</p> : null}</div>
            <ExportReview ed={ed} />
            <BulkImportReview ed={ed} />
            <ImportReport ed={ed} />
            <GearReview ed={ed} />
          </header>

          {/* Outside the <header> on purpose: a sticky element can only stick
              inside its own containing block, so a tab bar nested in the
              header would unstick the moment the header scrolled away. */}
          <TabBar tab={tab} setTab={changeTab} enabledTabs={shownTabs(d)} />

          <div id="character-panels" key={`${ch.id}-${searchRequest?.serial ?? 0}`}>
            <TabPanels
              tab={tab}
              panel={panel}
              sheetLayout={sheetLayout}
              onPortraitFile={onPortraitFile}
              setTab={changeTab}
            />
          </div>
          <AppFooter />
        </main>

        <CharacterSidebar
          catalog={catalog}
          character={ch}
          d={d}
          tr={tr}
          error={error}
          patch={patch}
        />
      </div>
    </BooksProvider>
  );
}
