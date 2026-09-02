import type { SheetData } from "@/lib/character/sheet-data";

/** Static, pen-and-paper condition monitor for the print layout: physical +
 * stun box grids with a −1 marker every third box, physical overflow boxes
 * (⌈BOD/2⌉) and the per-turn recovery figures. Nothing here is interactive —
 * the boxes are for filling in by hand at the table. */
export function PrintConditionMonitor(s: SheetData) {
  const { d, totals } = s;
  const physical = d.condition_monitor.physical || 0;
  const stun = d.condition_monitor.stun || 0;
  const overflow = Math.max(0, Math.ceil((totals.BOD || 0) / 2));
  const recovery = d.cm_recovery;

  const boxes = (count: number, offset = 0) =>
    Array.from({ length: count }, (_, i) => {
      const n = offset + i + 1;
      const penalty = n % 3 === 0;
      return (
        <span className={`cm-box${penalty ? " cm-box--mark" : ""}`} key={n}>
          {penalty ? <em>−{n / 3}</em> : null}
        </span>
      );
    });

  return (
    <section className="sheet-section sheet-section--print print-cm">
      <h3>コンディションモニター</h3>
      <div className="print-cm-track">
        <div className="print-cm-label">
          物理 <b>{physical}</b>
          {recovery ? <span className="sheet-dim"> 回復 {recovery.physical}/日</span> : null}
        </div>
        <div className="print-cm-boxes">{boxes(physical)}</div>
      </div>
      {overflow ? (
        <div className="print-cm-track">
          <div className="print-cm-label">
            オーバーフロー <b>{overflow}</b>
          </div>
          <div className="print-cm-boxes print-cm-boxes--overflow">{boxes(overflow)}</div>
        </div>
      ) : null}
      <div className="print-cm-track">
        <div className="print-cm-label">
          スタン <b>{stun}</b>
          {recovery ? <span className="sheet-dim"> 回復 {recovery.stun}/時間</span> : null}
        </div>
        <div className="print-cm-boxes">{boxes(stun)}</div>
      </div>
    </section>
  );
}
