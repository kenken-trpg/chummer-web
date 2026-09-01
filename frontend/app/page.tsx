"use client";

import { useEffect, useRef, useState } from "react";
import CharacterSheet, { type SheetLayout } from "@/components/CharacterSheet";
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
import { api, type CharacterSummary } from "@/lib/api";
import { buildChatPalette, buildCocofolia, buildCocofoliaConjured } from "@/lib/cocofolia";
import type { Tab } from "@/lib/character/constants";
import { useCharacterHistory } from "@/lib/character/history";
import { useSheetLayout } from "@/lib/character/useSheetLayout";
import { useKeyboardShortcuts } from "@/lib/character/useKeyboardShortcuts";
import type { Catalog, Character } from "@/lib/types";
import { makeT } from "@/lib/ui-strings";

export default function Page() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [ch, setCh] = useState<Character | null>(null);
  const [tab, setTab] = useState<Tab>("priority");
  const [error, setError] = useState<string | null>(null);
  const [sheetLayout, setSheetLayout] = useSheetLayout();
  const fileRef = useRef<HTMLInputElement>(null);
  const busy = useRef(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [roster, setRoster] = useState<CharacterSummary[]>([]);
  const history = useCharacterHistory();
  const lastCommitted = useRef<Character | null>(null);

  function remember(c: Character) {
    setCh(c);
    lastCommitted.current = c;
    history.reset();
    try {
      localStorage.setItem("lastCharacterId", c.id);
    } catch {}
  }
  async function refreshRoster() {
    setRoster(await api.list().catch(() => []));
  }

  useEffect(() => {
    (async () => {
      try {
        const [cat, list] = await Promise.all([api.catalog(), api.list().catch(() => [])]);
        setCatalog(cat);
        setRoster(list);
        let last: string | null = null;
        try {
          last = localStorage.getItem("lastCharacterId");
        } catch {}
        let opened: Character | null = null;
        if (last && list.some((r) => r.id === last)) {
          opened = await api.get(last).catch(() => null);
        }
        if (opened) {
          remember(opened);
        } else {
          remember(await api.create("Runner"));
          void refreshRoster();
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "起動に失敗しました");
      }
    })();
    // one-time bootstrap: load catalog + roster, then open the last / a new
    // character. `remember` is stable enough for a mount-only effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openCharacter(id: string) {
    if (!id || id === ch?.id) return;
    try {
      remember(await api.get(id));
      setTab("priority");
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読込に失敗しました");
    }
  }
  async function newCharacter() {
    remember(await api.create("Runner"));
    setTab("priority");
    void refreshRoster();
  }
  async function deleteCurrent() {
    if (!ch) return;
    if (!window.confirm(`「${ch.name || "無名"}」を削除しますか？`)) return;
    const others = roster.filter((r) => r.id !== ch.id);
    await api.remove(ch.id).catch(() => {});
    if (others[0]) await openCharacter(others[0].id);
    else await newCharacter();
    void refreshRoster();
  }
  async function duplicateCurrent() {
    if (!ch) return;
    const name = window.prompt("複製後の名前", `${ch.name || "無名"} のコピー`);
    if (name === null) return;
    try {
      const { id: _id, derived: _d, ...rest } = ch;
      void _id;
      void _d;
      remember(await api.import({ ...rest, name: name || `${ch.name || "無名"} のコピー` }));
      setTab("priority");
      void refreshRoster();
    } catch (e) {
      setError(e instanceof Error ? e.message : "複製に失敗しました");
    }
  }

  async function patch(body: Record<string, unknown>) {
    if (!ch || busy.current) return;
    busy.current = true;
    const base = lastCommitted.current ?? ch;
    try {
      const next = await api.patch(ch.id, body);
      history.record(base);
      setCh(next);
      lastCommitted.current = next;
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      busy.current = false;
    }
  }

  async function restoreSnapshot(snap: Character) {
    if (busy.current) return;
    busy.current = true;
    try {
      const { id: _id, derived: _d, ...body } = snap;
      void _id;
      void _d;
      const next = await api.patch(snap.id, body as Record<string, unknown>);
      setCh(next);
      lastCommitted.current = next;
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "取り消しに失敗しました");
    } finally {
      busy.current = false;
    }
  }

  async function undo() {
    if (!ch || busy.current) return;
    const snap = history.stepBack(lastCommitted.current ?? ch);
    if (snap) await restoreSnapshot(snap);
  }
  async function redo() {
    if (!ch || busy.current) return;
    const snap = history.stepForward(lastCommitted.current ?? ch);
    if (snap) await restoreSnapshot(snap);
  }
  useKeyboardShortcuts(undo, redo);

  const tr = (name: string) => catalog?.translations[name] || name;
  const t = makeT(catalog);

  function download() {
    if (!ch) return;
    const blob = new Blob([JSON.stringify(ch, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${ch.name || "character"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function downloadChum5() {
    if (!ch) return;
    // hit the .chum5 export endpoint via an anchor so the browser handles the
    // Content-Disposition download (not client-side navigation).
    const a = document.createElement("a");
    a.href = `/api/characters/${ch.id}/chummer`;
    a.click();
  }

  async function copyText(text: string, tag: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(tag);
    setTimeout(() => setCopied(null), 2000);
  }

  async function onImport(file: File) {
    setError(null);
    try {
      if (/\.chum5(lz)?$/i.test(file.name)) {
        const { character, warnings } = await api.importChummer(await file.arrayBuffer());
        remember(character);
        setTab("priority");
        if (warnings.length) {
          setError(
            `取り込み時の未対応 ${warnings.length}件 — ` + warnings.slice(0, 15).join(" / "),
          );
        }
      } else {
        remember(await api.import(JSON.parse(await file.text())));
        setTab("priority");
      }
      void refreshRoster();
    } catch (e) {
      setError(e instanceof Error ? e.message : "読込に失敗しました");
    }
  }

  async function onPortraitFile(file: File) {
    if (!ch) return;
    if (!/^image\//.test(file.type)) {
      setError("画像ファイルを選んでください");
      return;
    }
    if (file.size > 3_000_000) {
      setError("画像が大きすぎます（3MB まで）");
      return;
    }
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(String(r.result || ""));
        r.onerror = () => reject(r.error ?? new Error("読込に失敗しました"));
        r.readAsDataURL(file);
      });
      await patch({ portrait: dataUrl });
    } catch (e) {
      setError(e instanceof Error ? e.message : "画像の読込に失敗しました");
    }
  }

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

          <div className="toolbar">
            <select
              className="btn"
              value={ch.id}
              onChange={(e) =>
                e.target.value === "__new__" ? newCharacter() : openCharacter(e.target.value)
              }
              title="保存済みキャラクター"
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
              title={
                ch.career || d.career ? "作成モードに戻す" : "作成完了 → 残カルマ／ニューエンで成長"
              }
              onClick={() => {
                const next = !(ch.career || d.career);
                if (next && (d.errors || []).length) {
                  const ok = window.confirm(
                    "作成エラーが残っています。このままキャリアに進みますか？",
                  );
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
                >
                  <option value="standard">標準</option>
                  <option value="compact">コンパクト</option>
                  <option value="text">テキスト</option>
                </select>
                <button
                  className="btn primary"
                  onClick={() => window.print()}
                  title="印刷。ダイアログで「PDF として保存」も選べます"
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
          <div className="no-print sheet-notes-edit">
            <label>記述</label>
            <div className="portrait-edit">
              {ch.portrait ? (
                <img className="portrait-thumb" src={ch.portrait} alt="ポートレート" />
              ) : (
                <div className="portrait-thumb portrait-empty">画像なし</div>
              )}
              <div className="portrait-edit-controls">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void onPortraitFile(f);
                    e.target.value = "";
                  }}
                />
                {ch.portrait ? (
                  <button
                    className="btn"
                    type="button"
                    onClick={() => void patch({ portrait: "" })}
                  >
                    画像を削除
                  </button>
                ) : null}
                <span className="muted">.chum5 の mugshot と相互変換。3MB まで。</span>
              </div>
            </div>
            <div className="sheet-desc-grid">
              {(
                [
                  ["age", "年齢"],
                  ["sex", "性別"],
                  ["height", "身長"],
                  ["weight", "体重"],
                  ["eyes", "目"],
                  ["hair", "髪"],
                  ["skin", "肌"],
                  ["concept", "コンセプト"],
                ] as const
              ).map(([field, label]) => (
                <label key={field}>
                  {label}
                  <input
                    defaultValue={(ch[field] as string) || ""}
                    key={`${ch.id}-${field}`}
                    onBlur={(e) => {
                      if ((e.target.value || "") !== ((ch[field] as string) || ""))
                        patch({ [field]: e.target.value });
                    }}
                  />
                </label>
              ))}
            </div>
            {(
              [
                ["appearance", "容姿"],
                ["background", "背景"],
                ["notes", "メモ"],
              ] as const
            ).map(([field, label]) => (
              <div key={field} className="sheet-notes-edit" style={{ margin: "8px 0 0" }}>
                <label>{label}</label>
                <textarea
                  rows={field === "notes" ? 3 : 2}
                  defaultValue={(ch[field] as string) || ""}
                  key={`${ch.id}-${field}`}
                  placeholder={
                    field === "notes"
                      ? "GM 用メモ・運用メモなど。シートと .chum5 書き出しに反映されます。"
                      : ""
                  }
                  onBlur={(e) => {
                    if ((e.target.value || "") !== ((ch[field] as string) || ""))
                      patch({ [field]: e.target.value });
                  }}
                />
              </div>
            ))}
          </div>
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
