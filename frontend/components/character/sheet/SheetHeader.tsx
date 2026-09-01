import type { SheetData } from "@/lib/character/sheet-data";

export function SheetHeader(s: SheetData) {
  const { character, d, tr } = s;
  return (
    <header className="sheet-header">
      <div>
        <p className="sheet-kicker">
          Shadowrun 5e キャラクターシート
          {character.career || d.career ? " ・ キャリア" : " ・ 作成"}
        </p>
        <h2 className="sheet-name">{character.name || "無名のランナー"}</h2>
        <p className="sheet-meta">
          {tr(character.metatype)}
          {character.metavariant ? ` / ${tr(character.metavariant)}` : ""}
          {" ・ "}
          {character.talent || "Mundane"}
          {d.tradition ? ` ・ ${tr(d.tradition.name)}` : ""}
          {d.stream ? ` ・ ${tr(d.stream.name)}` : ""}
          {d.mentor ? ` ・ メンター ${tr(d.mentor.name)}` : ""}
        </p>
      </div>
      <div className="sheet-header-stats">
        <div>
          <span>アーマー</span>
          <b>{d.armor}</b>
        </div>
        <div>
          <span>エッセンス</span>
          <b>{d.essence}</b>
        </div>
        <div>
          <span>ニューエン</span>
          <b>{(d.nuyen ?? 0).toLocaleString()}¥</b>
        </div>
        <div>
          <span>カルマ残</span>
          <b>
            {d.karma?.remaining ?? 0}/{d.karma?.pool ?? 0}
          </b>
        </div>
        {character.career || d.career ? (
          <>
            <div>
              <span>SC</span>
              <b>{d.street_cred || 0}</b>
            </div>
            <div>
              <span>悪名</span>
              <b>{d.notoriety || 0}</b>
            </div>
            <div>
              <span>周知度</span>
              <b>{d.public_awareness || 0}</b>
            </div>
          </>
        ) : null}
      </div>
    </header>
  );
}
