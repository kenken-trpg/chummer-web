import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function KnowledgeSection(s: SheetData) {
  const { tr, totals, knowledge } = s;
  return (
    <Section title="知識技能" empty={!knowledge.length}>
      <table className="sheet-table">
        <thead>
          <tr>
            <th>知識</th>
            <th>分類</th>
            <th>R</th>
            <th>プール</th>
            <th>専門化</th>
          </tr>
        </thead>
        <tbody>
          {knowledge.map((row) => {
            const attr = totals[row.attribute] || 0;
            const rating = Math.max(row.rating || 0, row.skillsoft || 0);
            return (
              <tr key={`${row.category}-${row.name}`}>
                <td className="left">
                  {tr(row.name)}
                  {row.native ? "（母語）" : ""}
                  {(row.skillsoft || 0) > row.rating ? " *" : ""}
                </td>
                <td>{tr(row.category)}</td>
                <td>{rating}</td>
                <td>
                  <b>{rating + attr}</b>
                </td>
                <td className="left">{row.spec ? tr(row.spec) : ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Section>
  );
}
