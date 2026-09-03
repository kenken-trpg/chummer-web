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
  return (
    <div className="toolbar">
      <select
        className="btn"
        value={ch.id}
        onChange={(e) =>
          e.target.value === "__new__" ? newCharacter() : openCharacter(e.target.value)
        }
        title="保存済みキャラクター"
        aria-label="保存済みキャラクター"
      >
        {!roster.some((r) => r.id === ch.id) ? (
          <option value={ch.id}>{ch.name || "無名"}（未保存）</option>
        ) : null}
        {roster.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name || "無名"} ・ {tr(r.metatype)}
            {r.career ? "（キャリア）" : ""}
          </option>
        ))}
        <option value="__new__">＋ 新規キャラ</option>
      </select>
      <button className="btn" onClick={duplicateCurrent} title="名前を付けて複製">
        複製
      </button>
      <button className="btn" onClick={deleteCurrent} title="表示中のキャラクターを削除">
        削除
      </button>
      <button
        className="btn"
        onClick={() => void undo()}
        disabled={!history.counts.undo}
        title="元に戻す (Ctrl/⌘+Z)"
      >
        ↶ 元に戻す{history.counts.undo ? `（${history.counts.undo}）` : ""}
      </button>
      <button
        className="btn"
        onClick={() => void redo()}
        disabled={!history.counts.redo}
        title="やり直し (Ctrl/⌘+Shift+Z)"
      >
        ↷ やり直し{history.counts.redo ? `（${history.counts.redo}）` : ""}
      </button>
      <input
        value={ch.name}
        aria-label="キャラクター名"
        onChange={(e) => setCh({ ...ch, name: e.target.value })}
        onBlur={(e) => patch({ name: e.target.value }).then(refreshRoster)}
      />
      <button className="btn primary" onClick={download}>
        JSON保存
      </button>
      <button
        className="btn"
        onClick={downloadChum5}
        title="Chummer5a で開ける .chum5（XML）で書き出す"
      >
        .chum5書出
      </button>
      <button className="btn" onClick={() => fileRef.current?.click()}>
        読込 (JSON/.chum5)
      </button>
      <button
        className="btn"
        onClick={() => void copyShareLink()}
        title="読み取り専用の共有リンクをコピー。キャラは URL に埋め込まれ、サーバーには保存されません（ポートレートは含みません）"
      >
        {copied === "share" ? ui("share.copied") : ui("share.copy")}
      </button>
      <button
        className="btn"
        onClick={() => catalog && copyText(buildCocofolia(ch, catalog, tr), "cc")}
        title="ココフォリアのコマ JSON をコピー（貼り付けで取り込み）。判定は BCDice の ShadowRun5"
      >
        {copied === "cc" ? "コピー ✓" : "ココフォリア"}
      </button>
      <button
        className="btn"
        onClick={() => catalog && copyText(buildChatPalette(ch, catalog, tr), "cp")}
        title="チャットパレット（BCDice ShadowRun5 のコマンド一覧）をコピー"
      >
        {copied === "cp" ? "コピー ✓" : "チャットパレット"}
      </button>
      {d.spirits?.some((s) => s.bound) || d.sprites?.some((s) => s.registered) ? (
        <button
          className="btn"
          onClick={() => catalog && copyText(buildCocofoliaConjured(ch, catalog, tr), "cs")}
          title="束縛済み精霊／登録スプライトを、それぞれ別のココフォリアのコマ（JSON 配列）として書き出す"
        >
          {copied === "cs" ? "コピー ✓" : "精霊コマ"}
        </button>
      ) : null}
      <button
        className={`btn ${ch.career || d.career ? "primary" : ""}`}
        title={ch.career || d.career ? "作成モードに戻す" : "作成完了 → 残カルマ／ニューエンで成長"}
        onClick={() => {
          const next = !(ch.career || d.career);
          if (next && (d.errors || []).length) {
            const ok = window.confirm("作成エラーが残っています。このままキャリアに進みますか？");
            if (!ok) return;
          }
          patch({ career: next });
        }}
      >
        {ch.career || d.career ? "キャリア中" : "作成完了（キャリア）"}
      </button>
      {tab === "sheet" ? (
        <>
          <select
            className="btn"
            value={sheetLayout}
            onChange={(e) => setSheetLayout(e.target.value as SheetLayout)}
            title="シートのレイアウト"
            aria-label={ui("share.layout")}
          >
            <option value="standard">{ui("sheet.layout.standard")}</option>
            <option value="compact">{ui("sheet.layout.compact")}</option>
            <option value="text">{ui("sheet.layout.text")}</option>
            <option value="print">{ui("sheet.layout.print")}</option>
          </select>
          <button
            className="btn primary"
            onClick={printSheet}
            title="印刷用レイアウトに切り替えて印刷。ダイアログで「PDF として保存」も選べます"
          >
            印刷 / PDF
          </button>
        </>
      ) : (
        <button className="btn" onClick={() => setTab("sheet")}>
          シート表示
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
