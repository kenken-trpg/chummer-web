import { HelpTip } from "@/components/help/HelpTip";
import { useState } from "react";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

/** In Debt (RF p.156) in career mode: what is left of the loan, and the
 *  payments made towards it. A payment is spent like a purchase — the engine
 *  takes it off the nuyen left — so all this block writes is the list. */
export function SidebarDebt({ career, d, patch, ui }: SidebarBlockProps) {
  const [amount, setAmount] = useState(0);
  const debt = d.debt;
  const payments = d.debt_payments || [];
  if (!career || !patch || !debt || (!debt.principal && !payments.length)) return null;

  const pay = () => {
    const nuyen = Math.min(Math.max(0, Number(amount) || 0), debt.remaining);
    if (!nuyen) return;
    patch({ debt_payments: [...payments, { id: crypto.randomUUID(), nuyen }] });
    setAmount(0);
  };

  const remove = (id: string) => {
    patch({ debt_payments: payments.filter((row) => row.id !== id) });
  };

  return (
    <div className="career-panel">
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.debtLeft") })}
            lines={[{ label: ui("help.side.debt") }, { label: ui("help.side.debtPayment") }]}
          >
            {ui("side.debtLeft")}
          </HelpTip>
        </span>
        <b>
          {debt.remaining.toLocaleString()}¥ / {debt.principal.toLocaleString()}¥
        </b>
      </div>
      {payments.map((row) => (
        <div className="stat" key={row.id}>
          <span className="muted">
            {ui("side.debtPayment")} · {row.nuyen.toLocaleString()}¥
          </span>
          <button
            type="button"
            className="btn danger"
            style={{ padding: "2px 6px", fontSize: "0.75rem" }}
            aria-label={`${ui("side.debtPayment")} ${row.nuyen.toLocaleString()}¥: ${ui("side.deleteReward")}`}
            onClick={() => remove(row.id)}
          >
            {ui("side.deleteReward")}
          </button>
        </div>
      ))}
      {debt.remaining > 0 ? (
        <>
          <div className="stat">
            <span>¥</span>
            <input
              type="number"
              min={0}
              max={debt.remaining}
              step={1000}
              aria-label={ui("side.debtAmount")}
              value={amount}
              onChange={(e) => setAmount(Math.max(0, Number(e.target.value) || 0))}
              style={{ width: 96 }}
            />
          </div>
          <button type="button" className="btn" onClick={pay}>
            {ui("side.payDebt")}
          </button>
        </>
      ) : null}
    </div>
  );
}
