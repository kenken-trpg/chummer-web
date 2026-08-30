"use client";

import { useEffect, useRef, useState } from "react";
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
import { api } from "@/lib/api";
import type { Tab } from "@/lib/character/constants";
import type { Catalog, Character } from "@/lib/types";
import { makeT } from "@/lib/ui-strings";

export default function Page() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [ch, setCh] = useState<Character | null>(null);
  const [tab, setTab] = useState<Tab>("priority");
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const busy = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        const [cat, created] = await Promise.all([api.catalog(), api.create("Runner")]);
        setCatalog(cat);
        setCh(created);
      } catch (e) {
        setError(e instanceof Error ? e.message : "起動に失敗しました");
      }
    })();
  }, []);

  async function patch(body: Record<string, unknown>) {
    if (!ch || busy.current) return;
    busy.current = true;
    try {
      setCh(await api.patch(ch.id, body));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      busy.current = false;
    }
  }

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

  async function onImport(file: File) {
    const payload = JSON.parse(await file.text());
    setCh(await api.import(payload));
  }

  if (error && !ch) {
    return <div className="main"><p className="errors">{error}</p></div>;
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
          <p className="sub">非公式 Shadowrun 5e キャラクター作成。Catalyst / Topps 非提携。データは Chummer5a (GPL-3.0)。</p>

          <div className="toolbar">
            <input value={ch.name} onChange={(e) => setCh({ ...ch, name: e.target.value })} onBlur={(e) => patch({ name: e.target.value })} />
            <button className="btn primary" onClick={download}>JSON保存</button>
            <button className="btn" onClick={() => fileRef.current?.click()}>JSON読込</button>
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
              <button className="btn primary" onClick={() => window.print()}>印刷</button>
            ) : (
              <button className="btn" onClick={() => setTab("sheet")}>シート表示</button>
            )}
            <input ref={fileRef} type="file" accept="application/json" hidden onChange={(e) => e.target.files && onImport(e.target.files[0])} />
          </div>

          <div className="tabs">
            {([
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
              ...(d.enabled_tabs.includes("initiation") ? [["initiation", "イニシエーション"] as const] : []),
              ...(d.enabled_tabs.includes("submersion") ? [["submersion", "サブマージョン"] as const] : []),
              ...(d.enabled_tabs.includes("adept") ? [["adept", "アデプト"] as const] : []),
              ...(d.enabled_tabs.includes("spells") ? [["spells", "術式"] as const] : []),
              ...(d.enabled_tabs.includes("spirits") ? [["spirits", "精霊"] as const] : []),
              ...(d.enabled_tabs.includes("foci") ? [["foci", "フォーカス"] as const] : []),
              ...(d.enabled_tabs.includes("complexforms") ? [["complexforms", "複合体"] as const] : []),
              ...(d.enabled_tabs.includes("sprites") ? [["sprites", "スプライト"] as const] : []),
              ["sheet", "シート"],
            ] as const).map(([k, label]) => (
              <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>{label}</button>
            ))}
          </div>
        </div>

        {tab === "sheet" && <CharacterSheet character={ch} catalog={catalog} tr={tr} />}
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
        {tab === "initiation" && d.enabled_tabs.includes("initiation") && <InitiationTab {...panel} />}
        {tab === "submersion" && d.enabled_tabs.includes("submersion") && <SubmersionTab {...panel} />}
        {tab === "adept" && d.enabled_tabs.includes("adept") && <AdeptTab {...panel} />}
        {tab === "spells" && d.enabled_tabs.includes("spells") && <SpellsTab {...panel} />}
        {tab === "spirits" && d.enabled_tabs.includes("spirits") && <SpiritsTab {...panel} />}
        {tab === "foci" && d.enabled_tabs.includes("foci") && <FociTab {...panel} />}
        {tab === "complexforms" && d.enabled_tabs.includes("complexforms") && <ComplexFormsTab {...panel} />}
        {tab === "sprites" && d.enabled_tabs.includes("sprites") && <SpritesTab {...panel} />}
      </div>

      <CharacterSidebar catalog={catalog} character={ch} d={d} tr={tr} error={error} patch={patch} />
    </div>
  );
}
