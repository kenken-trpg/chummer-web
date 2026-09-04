import type { SheetData } from "@/lib/character/sheet-data";
import { useUiText } from "@/lib/i18n";

export function SheetHeader(s: SheetData) {
  const { character, d, tr } = s;
  const { ui } = useUiText();
  return (
    <header className="sheet-header">
      <div>
        <p className="sheet-kicker">
          {ui("sheet.kicker")}
          {character.career || d.career ? ui("sheet.modeCareer") : ui("sheet.modeChargen")}
        </p>
        <h2 className="sheet-name">{character.name || ui("sheet.unnamed")}</h2>
        <p className="sheet-meta">
          {tr(character.metatype)}
          {character.metavariant ? ` / ${tr(character.metavariant)}` : ""}
          {" ・ "}
          {character.talent || "Mundane"}
          {d.tradition ? ` ・ ${tr(d.tradition.name)}` : ""}
          {d.stream ? ` ・ ${tr(d.stream.name)}` : ""}
          {d.mentor ? ui("sheet.mentor", { name: tr(d.mentor.name) }) : ""}
        </p>
      </div>
      <div className="sheet-header-stats">
        <div>
          <span>{ui("common.armor")}</span>
          <b>{d.armor}</b>
        </div>
        <div>
          <span>{ui("common.essence")}</span>
          <b>{d.essence}</b>
        </div>
        <div>
          <span>{ui("common.nuyen")}</span>
          <b>{(d.nuyen ?? 0).toLocaleString()}¥</b>
        </div>
        <div>
          <span>{ui("sheet.karmaLeft")}</span>
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
              <span>{ui("common.notoriety")}</span>
              <b>{d.notoriety || 0}</b>
            </div>
            <div>
              <span>{ui("common.publicAwareness")}</span>
              <b>{d.public_awareness || 0}</b>
            </div>
          </>
        ) : null}
      </div>
    </header>
  );
}
