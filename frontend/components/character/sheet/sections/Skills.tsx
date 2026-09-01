import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function SkillsSection(s: SheetData) {
  const { tr, totals, activeSkills, groups, exotic } = s;
  return (
    <Section title="技能" empty={!activeSkills.length && !groups.length && !exotic.length}>
      {groups.length ? (
        <p className="sheet-note">
          グループ:{" "}
          {groups
            .map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? ` (+${g.bonus})` : ""}`)
            .join(" ・ ")}
        </p>
      ) : null}
      <table className="sheet-table">
        <thead>
          <tr>
            <th>技能</th>
            <th>能力値</th>
            <th>R</th>
            <th>プール</th>
            <th>専門化</th>
          </tr>
        </thead>
        <tbody>
          {activeSkills.map((row) => (
            <tr key={row.name}>
              <td className="left">
                {tr(row.name)}
                {row.soft ? " *" : ""}
              </td>
              <td>{row.attribute}</td>
              <td>{row.rating}</td>
              <td>
                <b>{row.pool}</b>
              </td>
              <td className="left">{row.spec ? tr(row.spec) : ""}</td>
            </tr>
          ))}
          {exotic.map((row) => {
            const attr = totals[row.attribute] || 0;
            return (
              <tr key={row.id}>
                <td className="left">{tr(row.label || row.skill_name)}</td>
                <td>{row.attribute}</td>
                <td>{row.rating}</td>
                <td>
                  <b>{row.rating + attr}</b>
                </td>
                <td className="left">{row.extra ? tr(row.extra) : ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {activeSkills.some((row) => row.soft) ? <p className="sheet-note">* スキルソフト</p> : null}
    </Section>
  );
}
