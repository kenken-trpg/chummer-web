import type { RefObject } from "react";
import type { Tab } from "@/lib/character/constants";
import type { SheetLayout } from "@/components/CharacterSheet";
import type { Catalog, Character } from "@/lib/types";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { buildChatPalette, buildCocofolia, buildCocofoliaConjured } from "@/lib/cocofolia";
import { usePrintSheet } from "@/lib/character/usePrintSheet";
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
    copyText,
    copyShareLink,
    refreshRoster,
  } = ed;
  const d = ch.derived;
  const { ui } = useUiText();
  const printSheet = usePrintSheet(sheetLayout, setSheetLayout);
  const inCareer = ch.career || d.career;
  return (
    <div className="toolbar">
      <select
        className="btn"
        value={ch.id}
        onChange={(e) =>
          e.target.value === "__new__" ? newCharacter() : openCharacter(e.target.value)
        }
        title={ui("toolbar.roster")}
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
      <button className="btn" onClick={duplicateCurrent} title={ui("toolbar.duplicateHint")}>
        {ui("toolbar.duplicate")}
      </button>
      <button className="btn" onClick={deleteCurrent} title={ui("toolbar.deleteHint")}>
        {ui("toolbar.delete")}
      </button>
      <button
        className="btn"
        onClick={() => void undo()}
        disabled={!history.counts.undo}
        title={ui("toolbar.undoHint")}
      >
        {history.counts.undo
          ? ui("toolbar.undoCount", { count: history.counts.undo })
          : ui("toolbar.undo")}
      </button>
      <button
        className="btn"
        onClick={() => void redo()}
        disabled={!history.counts.redo}
        title={ui("toolbar.redoHint")}
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
      <button className="btn" onClick={downloadChum5} title={ui("toolbar.exportChum5Hint")}>
        {ui("toolbar.exportChum5")}
      </button>
      <button className="btn" onClick={() => fileRef.current?.click()}>
        {ui("toolbar.import")}
      </button>
      <button className="btn" onClick={() => void copyShareLink()} title={ui("toolbar.shareHint")}>
        {copied === "share" ? ui("share.copied") : ui("share.copy")}
      </button>
      <button
        className="btn"
        onClick={() => catalog && copyText(buildCocofolia(ch, catalog, tr), "cc")}
        title={ui("toolbar.cocofoliaHint")}
      >
        {copied === "cc" ? ui("share.copied") : ui("toolbar.cocofolia")}
      </button>
      <button
        className="btn"
        onClick={() => catalog && copyText(buildChatPalette(ch, catalog, tr), "cp")}
        title={ui("toolbar.chatPaletteHint")}
      >
        {copied === "cp" ? ui("share.copied") : ui("toolbar.chatPalette")}
      </button>
      {d.spirits?.some((s) => s.bound) || d.sprites?.some((s) => s.registered) ? (
        <button
          className="btn"
          onClick={() => catalog && copyText(buildCocofoliaConjured(ch, catalog, tr), "cs")}
          title={ui("toolbar.conjuredHint")}
        >
          {copied === "cs" ? ui("share.copied") : ui("toolbar.conjured")}
        </button>
      ) : null}
      <button
        className={`btn ${inCareer ? "primary" : ""}`}
        title={inCareer ? ui("toolbar.careerHint") : ui("toolbar.toCareerHint")}
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
      {tab === "sheet" ? (
        <>
          <select
            className="btn"
            value={sheetLayout}
            onChange={(e) => setSheetLayout(e.target.value as SheetLayout)}
            title={ui("toolbar.layoutHint")}
            aria-label={ui("share.layout")}
          >
            <option value="standard">{ui("sheet.layout.standard")}</option>
            <option value="compact">{ui("sheet.layout.compact")}</option>
            <option value="text">{ui("sheet.layout.text")}</option>
            <option value="print">{ui("sheet.layout.print")}</option>
          </select>
          <button className="btn primary" onClick={printSheet} title={ui("toolbar.printHint")}>
            {ui("share.print")}
          </button>
        </>
      ) : (
        <button className="btn" onClick={() => setTab("sheet")}>
          {ui("toolbar.showSheet")}
        </button>
      )}
      <input
        ref={fileRef}
        type="file"
        accept="application/json,.chum5,.chum5lz"
        hidden
        onChange={(e) => e.target.files && onImport(e.target.files[0])}
      />
    </div>
  );
}
