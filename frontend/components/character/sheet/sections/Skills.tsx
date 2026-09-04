import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function SkillsSection(s: SheetData) {
  const { tr, totals, activeSkills, groups, exotic } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.skills" empty={!activeSkills.length && !groups.length && !exotic.length}>
      {groups.length ? (
        <p className="sheet-note">
          {ui("sheet.groups", {
            list: groups
              .map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? ` (+${g.bonus})` : ""}`)
              .join(` ${ui("common.termSep")} `),
          })}
        </p>
      ) : null}
      <table className="sheet-table">
        <thead>
          <tr>
            <th>{ui("sheet.col.skill")}</th>
            <th>{ui("sheet.col.attribute")}</th>
            <th>R</th>
            <th>{ui("sheet.col.pool")}</th>
            <th>{ui("sheet.col.spec")}</th>
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
      {activeSkills.some((row) => row.soft) ? (
        <p className="sheet-note">{ui("sheet.skillsoftNote")}</p>
      ) : null}
    </Section>
  );
}
