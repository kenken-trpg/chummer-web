import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerEdit({ ch, career, patch }: SidebarBlockProps) {
  return (
    <>
      {career && patch ? (
        <div className="career-panel">
          <div className="stat">
            <span>SC 編集</span>
            <input
              type="number"
              min={0}
              value={ch.street_cred || 0}
              onChange={(e) => patch({ street_cred: Math.max(0, Number(e.target.value) || 0) })}
              style={{ width: 64 }}
            />
          </div>
          <div className="stat">
            <span>悪名ボーナス</span>
            <input
              type="number"
              value={ch.notoriety_bonus || 0}
              onChange={(e) => patch({ notoriety_bonus: Number(e.target.value) || 0 })}
              style={{ width: 64 }}
            />
          </div>
          <p className="muted">周知度 = ⌊(SC + max(悪名,0)) / 3⌋ + 品質修正</p>
        </div>
      ) : null}
    </>
  );
}
