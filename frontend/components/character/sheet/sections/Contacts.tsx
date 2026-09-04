import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function ContactsSection(s: SheetData) {
  const { d } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.contacts" empty={!(d.contacts || []).length}>
      <table className="sheet-table">
        <thead>
          <tr>
            <th>{ui("sheet.col.name")}</th>
            <th>{ui("sheet.col.role")}</th>
            <th>C</th>
            <th>L</th>
          </tr>
        </thead>
        <tbody>
          {(d.contacts || []).map((c) => (
            <tr key={c.id}>
              <td className="left">
                {c.name}
                {c.free ? " ★" : ""}
                {c.group ? " (G)" : ""}
              </td>
              <td className="left">{c.role || ""}</td>
              <td>{c.connection}</td>
              <td>{c.loyalty}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Section>
  );
}
