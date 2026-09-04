import type { SheetData } from "@/lib/character/sheet-data";
import { GradeList, Section } from "@/components/character/sheet/blocks";
import { cfDuration, cfTarget } from "@/lib/character/format";

export function ResonanceSection(s: SheetData) {
  const { tr, d, enabled } = s;
  return (
    <Section
      title="sheet.resonance"
      empty={!enabled.has("complexforms") && !enabled.has("sprites") && !enabled.has("submersion")}
    >
      {enabled.has("complexforms") && (d.complex_forms || []).length ? (
        <div className="sheet-block">
          <h4>
            複合体
            {d.fade_resist
              ? ` ・ フェード抵抗 ${d.fade_resist.pool}（${d.fade_resist.attrs}）`
              : ""}
          </h4>
          <ul className="sheet-list">
            {(d.complex_forms || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.label || item.name)}</b>
                {" ・ "}対象 {cfTarget(item.target)} / {cfDuration(item.duration)} / レベル{" "}
                {item.level} / FV {item.fv}
                {item.fade != null ? ` ・ フェード ${item.fade}${item.fade_code || ""}` : ""}
                {item.physical ? "（物理）" : ""}
                {item.extra ? `（${tr(item.extra)}）` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("sprites") && (d.sprites || []).length ? (
        <div className="sheet-block">
          <h4>スプライト</h4>
          <ul className="sheet-list">
            {(d.sprites || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}L{item.level}
                {item.services != null ? ` ・ サービス ${item.services}` : ""}
                {item.registered ? " ・ 登録" : " ・ コンパイル"}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("submersion") && (d.submersion?.grade || 0) > 0 ? (
        <div className="sheet-block">
          <h4>サブマージョン 等級 {d.submersion?.grade}</h4>
          {(d.submersion?.echoes || []).length ? (
            <GradeList items={d.submersion?.echoes || []} tr={tr} />
          ) : (
            <p className="sheet-note">エコー未選択</p>
          )}
        </div>
      ) : null}
    </Section>
  );
}
