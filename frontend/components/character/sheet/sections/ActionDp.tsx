import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function ActionDpSection(s: SheetData) {
  const { tr, d } = s;
  if (!(d.action_dice_pools || []).length) return null;
  return (
    <Section title="アクションDP">
      <ul className="sheet-list">
        {(d.action_dice_pools || []).map((row, idx) => (
          <li key={`${row.name}-${idx}`}>
            <b>{row.category ? `${row.category}: ${tr(row.name)}` : tr(row.name)}</b>
            <span className="sheet-dim">
              {" "}
              {row.bonus > 0 ? "+" : ""}
              {row.bonus}
            </span>
          </li>
        ))}
      </ul>
    </Section>
  );
}
