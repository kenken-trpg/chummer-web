import type { SheetData } from "@/lib/character/sheet-data";
import { useUiText } from "@/lib/i18n";

/** Static, pen-and-paper condition monitor for the print layout: physical +
 * stun box grids with a −1 marker every third box, physical overflow boxes
 * (⌈BOD/2⌉) and the per-turn recovery figures. Nothing here is interactive —
 * the boxes are for filling in by hand at the table.
 *
 * "Every third box" is the default; High Pain Tolerance and the drugs that
 * grant it push the first marker further out, Low Pain Tolerance moves every
 * marker in — so the markers are drawn from what the engine reports. */
export function PrintConditionMonitor(s: SheetData) {
  const { d, totals } = s;
  const { ui } = useUiText();
  const physical = d.condition_monitor.physical || 0;
  const stun = d.condition_monitor.stun || 0;
  const overflow = Math.max(0, Math.ceil((totals.BOD || 0) / 2));
  const recovery = d.cm_recovery;
  const threshold = Math.max(1, d.condition_monitor.threshold || 3);
  const ignored = Math.max(0, d.condition_monitor.threshold_offset || 0);

  const boxes = (count: number) =>
    Array.from({ length: count }, (_, i) => {
      const n = i + 1;
      const counted = n - ignored;
      const penalty = counted > 0 && counted % threshold === 0;
      return (
        <span className={`cm-box${penalty ? " cm-box--mark" : ""}`} key={n}>
          {penalty ? <em>−{counted / threshold}</em> : null}
        </span>
      );
    });

  return (
    <section className="sheet-section sheet-section--print print-cm">
      <h3>{ui("print.conditionMonitor")}</h3>
      <div className="print-cm-track">
        <div className="print-cm-label">
          {ui("print.physical")} <b>{physical}</b>
          {recovery ? (
            <span className="sheet-dim">{ui("print.recoveryDay", { n: recovery.physical })}</span>
          ) : null}
        </div>
        <div className="print-cm-boxes">{boxes(physical)}</div>
      </div>
      {overflow ? (
        <div className="print-cm-track">
          <div className="print-cm-label">
            {ui("print.overflow")} <b>{overflow}</b>
          </div>
          <div className="print-cm-boxes print-cm-boxes--overflow">{boxes(overflow)}</div>
        </div>
      ) : null}
      <div className="print-cm-track">
        <div className="print-cm-label">
          {ui("print.stun")} <b>{stun}</b>
          {recovery ? (
            <span className="sheet-dim">{ui("print.recoveryHour", { n: recovery.stun })}</span>
          ) : null}
        </div>
        <div className="print-cm-boxes">{boxes(stun)}</div>
      </div>
    </section>
  );
}
