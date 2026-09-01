import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

export function SidebarAttributes({ d, t }: SidebarBlockProps) {
  return (
    <>
      <h3>能力値</h3>
      {ATTRS.map((k) => {
        const hidden =
          (k === "MAG" && !d.enabled_tabs.includes("MAG")) ||
          (k === "RES" && !d.enabled_tabs.includes("RES"));
        if (hidden) return null;
        return (
          <div className="stat" key={k}>
            <span>{attrLabel(k, t)}</span>
            <b>
              {d.totals[k] ?? "-"}
              {(d.ware_attr_bonus?.[k] || 0) !== 0 ? (
                <span className="muted"> ウェア+{d.ware_attr_bonus![k]}</span>
              ) : null}
              {d.limb_replace && (k === "STR" || k === "AGI") ? (
                <span className="muted"> リム平均</span>
              ) : null}
            </b>
          </div>
        );
      })}
      {d.unimplemented_bonuses.length > 0 && (
        <p className="warn">未実装ボーナス {d.unimplemented_bonuses.length} 件（無視して継続）</p>
      )}
    </>
  );
}
