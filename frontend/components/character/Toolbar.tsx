import type { RefObject } from "react";
import type { Tab } from "@/lib/character/constants";
import { HelpTip } from "@/components/help/HelpTip";
import type { SheetLayout } from "@/components/CharacterSheet";
import type { Catalog, Character } from "@/lib/types";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { buildChatPalette, buildCocofolia, buildCocofoliaConjured } from "@/lib/cocofolia";
import { Menu } from "@/components/character/Menu";
import { usePrintSheet } from "@/lib/character/usePrintSheet";
import { useWareCompact } from "@/lib/character/useWareCompact";
import { useUiText } from "@/lib/i18n";

export function Toolbar({
  ed,
  ch,
  catalog,
  tab,
  setTab,
  sheetLayout,
  setSheetLayout,
  fileRef,
}: {
  ed: CharacterEditor;
  ch: Character;
  catalog: Catalog;
  tab: Tab;
  setTab: (t: Tab) => void;
  sheetLayout: SheetLayout;
  setSheetLayout: (v: SheetLayout) => void;
  fileRef: RefObject<HTMLInputElement | null>;
}) {
  const {
    roster,
    tr,
    history,
    copied,
    setCh,
    patch,
    undo,
    redo,
    openCharacter,
    newCharacter,
    deleteCurrent,
    duplicateCurrent,
    onImport,
    download,
    downloadChum5,
    downloadXlsx,
    downloadFvtt,
    downloadUdonarium,
    downloadUdonariumConjured,
    copyText,
    copyShareLink,
    refreshRoster,
  } = ed;
  const d = ch.derived;
  const { locale, ui } = useUiText();
  const printSheet = usePrintSheet(sheetLayout, setSheetLayout);
  const inCareer = ch.career || d.career;
  // a local switch, the same as the sheet's names-only one
  const [untrained, setUntrained] = useWareCompact("cocoUntrained");
  return (
    <div className="toolbar">
      <select
        className="btn"
        value={ch.id}
        onChange={(e) =>
          e.target.value === "__new__" ? newCharacter() : openCharacter(e.target.value)
        }
        aria-label={ui("toolbar.roster")}
      >
        {!roster.some((r) => r.id === ch.id) ? (
          <option value={ch.id}>
            {ch.name || ui("toolbar.unnamed")}
            {ui("toolbar.unsaved")}
          </option>
        ) : null}
        {roster.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name || ui("toolbar.unnamed")} ・ {tr(r.metatype)}
            {r.career ? ui("toolbar.careerTag") : ""}
          </option>
        ))}
        <option value="__new__">{ui("toolbar.newCharacter")}</option>
      </select>
      <button className="btn" onClick={duplicateCurrent}>
        {ui("toolbar.duplicate")}
      </button>
      <button className="btn" onClick={deleteCurrent}>
        {ui("toolbar.delete")}
      </button>
      <button
        className="btn"
        onClick={() => void undo()}
        disabled={!history.counts.undo}
        aria-keyshortcuts="Control+Z Meta+Z"
      >
        {history.counts.undo
          ? ui("toolbar.undoCount", { count: history.counts.undo })
          : ui("toolbar.undo")}
      </button>
      <button
        className="btn"
        onClick={() => void redo()}
        disabled={!history.counts.redo}
        aria-keyshortcuts="Control+Shift+Z Meta+Shift+Z"
      >
        {history.counts.redo
          ? ui("toolbar.redoCount", { count: history.counts.redo })
          : ui("toolbar.redo")}
      </button>
      <input
        value={ch.name}
        aria-label={ui("toolbar.name")}
        onChange={(e) => setCh({ ...ch, name: e.target.value })}
        onBlur={(e) => patch({ name: e.target.value }).then(refreshRoster)}
      />
      <button className="btn primary" onClick={download}>
        {ui("toolbar.saveJson")}
      </button>
      <HelpTip
        label={ui("help.open", { label: ui("toolbar.import") })}
        lines={[{ label: ui("help.toolbar.import") }]}
      >
        <button className="btn" onClick={() => fileRef.current?.click()}>
          {ui("toolbar.import")}
        </button>
      </HelpTip>
      <HelpTip
        label={ui("help.open", { label: ui("share.copy") })}
        lines={[{ label: ui("help.toolbar.share") }]}
      >
        <button className="btn" onClick={() => void copyShareLink()}>
          {copied === "share" ? ui("share.copied") : ui("share.copy")}
        </button>
      </HelpTip>
      {/* Everything above is what you reach for every session: save, load,
          share, print. The conversions below are a handful of buttons each
          used once in a while, and as a flat row they were most of the
          toolbar — so they live one click away instead. */}
      <Menu label={ui("toolbar.exportMenu")}>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.exportChum5") })}
          lines={[{ label: ui("help.toolbar.exportChum5") }]}
        >
          <button className="btn" onClick={downloadChum5}>
            {ui("toolbar.exportChum5")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.exportXlsx") })}
          lines={[{ label: ui("help.toolbar.exportXlsx") }]}
        >
          <button className="btn" onClick={() => void downloadXlsx()}>
            {ui("toolbar.exportXlsx")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.exportFvtt") })}
          lines={[{ label: ui("help.toolbar.exportFvtt") }]}
        >
          <button className="btn" onClick={() => void downloadFvtt()}>
            {ui("toolbar.exportFvtt")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.cocofolia") })}
          lines={[{ label: ui("help.toolbar.cocofolia") }]}
        >
          <button
            className="btn"
            onClick={() =>
              catalog && copyText(buildCocofolia(ch, catalog, tr, locale, { untrained }), "cc")
            }
          >
            {copied === "cc" ? ui("share.copied") : ui("toolbar.cocofolia")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.udonarium") })}
          lines={[{ label: ui("help.toolbar.udonarium") }]}
        >
          <button
            className="btn"
            onClick={() => catalog && void downloadUdonarium(catalog, tr, { untrained })}
          >
            {ui("toolbar.udonarium")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.chatPalette") })}
          lines={[{ label: ui("help.toolbar.chatPalette") }]}
        >
          <button
            className="btn"
            onClick={() =>
              catalog && copyText(buildChatPalette(ch, catalog, tr, locale, { untrained }), "cp")
            }
          >
            {copied === "cp" ? ui("share.copied") : ui("toolbar.chatPalette")}
          </button>
        </HelpTip>
        <HelpTip
          label={ui("help.open", { label: ui("toolbar.cocoUntrained") })}
          lines={[{ label: ui("help.toolbar.cocoUntrained") }]}
        >
          <label className="btn">
            <input
              type="checkbox"
              checked={untrained}
              onChange={(e) => setUntrained(e.target.checked)}
            />
            {ui("toolbar.cocoUntrained")}
          </label>
        </HelpTip>
        {d.spirits?.some((s) => s.bound) || d.sprites?.some((s) => s.registered) ? (
          <HelpTip
            label={ui("help.open", { label: ui("toolbar.conjured") })}
            lines={[{ label: ui("help.toolbar.conjured") }]}
          >
            <button
              className="btn"
              onClick={() =>
                catalog && copyText(buildCocofoliaConjured(ch, catalog, tr, locale), "cs")
              }
            >
              {copied === "cs" ? ui("share.copied") : ui("toolbar.conjured")}
            </button>
          </HelpTip>
        ) : null}
        {/* one button for everything the runner brings along — spirits, sprites,
            vehicles and drones — each kind as its own zip */}
        {d.spirits?.some((s) => s.bound) ||
        d.sprites?.some((s) => s.registered) ||
        d.vehicles?.length ||
        d.drones?.length ? (
          <HelpTip
            label={ui("help.open", { label: ui("toolbar.udonariumConjured") })}
            lines={[{ label: ui("help.toolbar.udonariumConjured") }]}
          >
            <button
              className="btn"
              onClick={() => catalog && downloadUdonariumConjured(catalog, tr)}
            >
              {ui("toolbar.udonariumConjured")}
            </button>
          </HelpTip>
        ) : null}
      </Menu>
      <HelpTip
        label={ui("help.open", { label: inCareer ? ui("toolbar.career") : ui("toolbar.toCareer") })}
        lines={[{ label: inCareer ? ui("help.toolbar.career") : ui("help.toolbar.toCareer") }]}
      >
        <button
          className={`btn ${inCareer ? "primary" : ""}`}
          onClick={() => {
            const next = !inCareer;
            if (next && (d.errors || []).length) {
              if (!window.confirm(ui("toolbar.careerConfirm"))) return;
            }
            patch({ career: next });
          }}
        >
          {inCareer ? ui("toolbar.career") : ui("toolbar.toCareer")}
        </button>
      </HelpTip>
      {tab === "sheet" ? (
        <>
          <select
            className="btn"
            value={sheetLayout}
            onChange={(e) => setSheetLayout(e.target.value as SheetLayout)}
            aria-label={ui("share.layout")}
          >
            <option value="standard">{ui("sheet.layout.standard")}</option>
            <option value="compact">{ui("sheet.layout.compact")}</option>
            <option value="text">{ui("sheet.layout.text")}</option>
            <option value="print">{ui("sheet.layout.print")}</option>
          </select>
          <HelpTip
            label={ui("help.open", { label: ui("share.print") })}
            lines={[{ label: ui("help.toolbar.print") }]}
          >
            <button className="btn primary" onClick={printSheet}>
              {ui("share.print")}
            </button>
          </HelpTip>
        </>
      ) : (
        <button className="btn" onClick={() => setTab("sheet")}>
          {ui("toolbar.showSheet")}
        </button>
      )}
      <input
        ref={fileRef}
        type="file"
        accept="application/json,.chum5,.chum5lz,.xlsx"
        hidden
        // named for the same reason the settings one is: the page now holds
        // more than one file input, so "the file input" is no longer a thing
        // a screen reader — or a test — can point at
        aria-label={ui("toolbar.import")}
        onChange={(e) => e.target.files && onImport(e.target.files[0])}
      />
    </div>
  );
}
