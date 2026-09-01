import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function ContactsSection(s: SheetData) {
  const { d } = s;
  return (
    <Section title="コンタクト" empty={!(d.contacts || []).length}>
      <table className="sheet-table">
        <thead>
          <tr>
            <th>名前</th>
            <th>役割</th>
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
