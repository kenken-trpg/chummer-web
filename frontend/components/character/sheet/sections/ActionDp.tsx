import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { actionLabel } from "@/lib/character/action-labels";
import { useUiText } from "@/lib/i18n";

export function ActionDpSection(s: SheetData) {
  const { tr, d } = s;
  const { ui } = useUiText();
  if (!(d.action_dice_pools || []).length) return null;
  return (
    <Section title="sheet.actionDp">
      <ul className="sheet-list">
        {(d.action_dice_pools || []).map((row, idx) => (
          <li key={`${row.name}-${idx}`}>
            {/* the category is a catalog word ("Matrix"), the action is ours */}
            <b>
              {row.category ? `${tr(row.category)}: ` : ""}
              {actionLabel(row.name, ui, tr)}
            </b>
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
