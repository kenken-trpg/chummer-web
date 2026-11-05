/**
 * In Debt's career block: what is left of the loan, and the payments that
 * brought it down. The engine does the sums; this block only shows them and
 * writes the payment list back.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { SidebarDebt } from "@/components/character/sidebar/SidebarDebt";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import type { Character } from "@/lib/types";

type Patch = (body: Record<string, unknown>) => void;

function renderBlock(
  over: { derived?: Record<string, unknown>; career?: boolean; patch?: Patch | null } = {},
) {
  const ch = makeCharacter({ career: true, derived: over.derived } as never);
  return render(
    <SidebarDebt
      catalog={makeCatalog()}
      ch={ch}
      d={ch.derived as Character["derived"]}
      tr={identityTr}
      t={(key) => key}
      ui={testUi}
      career={over.career ?? true}
      patch={over.patch === undefined ? () => {} : (over.patch ?? undefined)}
    />,
  );
}

const owing = {
  debt: { principal: 15000, paid: 4000, remaining: 11000 },
  debt_payments: [{ id: "p1", nuyen: 4000 }],
};
const amountField = () => screen.getByRole("spinbutton", { name: "返済額" });
const payButton = () => screen.getByRole("button", { name: "返済する" });

describe("<SidebarDebt>", () => {
  it("appears only for a career character who owes, and can write", () => {
    expect(
      renderBlock({ derived: { debt: { principal: 0, paid: 0, remaining: 0 } } }).container
        .textContent,
    ).toBe("");
    expect(renderBlock({ career: false, derived: owing }).container.textContent).toBe("");
    expect(renderBlock({ patch: null, derived: owing }).container.textContent).toBe("");
  });

  it("shows what is left of what was lent, and each payment", () => {
    renderBlock({ derived: owing });
    expect(screen.getByText("11,000¥ / 15,000¥")).toBeDefined();
    expect(screen.getByText(/返済 · 4,000¥/)).toBeDefined();
    expect(screen.getByRole("button", { name: "借金の残り の説明" })).toBeDefined();
  });

  it("adds a payment, no more than is left", () => {
    const patch = vi.fn();
    renderBlock({ patch, derived: owing });
    fireEvent.change(amountField(), { target: { value: "20000" } });
    fireEvent.click(payButton());
    expect(patch).toHaveBeenCalledWith({
      debt_payments: [
        { id: "p1", nuyen: 4000 },
        { id: expect.any(String), nuyen: 11000 },
      ],
    });
    expect((amountField() as HTMLInputElement).value).toBe("0");
  });

  it("will not log a payment of nothing", () => {
    const patch = vi.fn();
    renderBlock({ patch, derived: owing });
    fireEvent.change(amountField(), { target: { value: "-500" } });
    fireEvent.click(payButton());
    expect(patch).not.toHaveBeenCalled();
  });

  it("deletes a payment", () => {
    const patch = vi.fn();
    renderBlock({ patch, derived: owing });
    fireEvent.click(screen.getByRole("button", { name: "返済 4,000¥: 削除" }));
    expect(patch).toHaveBeenCalledWith({ debt_payments: [] });
  });

  // Paid off: the payments stay listed, so one can still be taken back, but
  // there is nothing left to pay.
  it("stops offering to pay once the debt is paid off", () => {
    renderBlock({
      derived: {
        debt: { principal: 5000, paid: 5000, remaining: 0 },
        debt_payments: [{ id: "p1", nuyen: 5000 }],
      },
    });
    expect(screen.getByText("0¥ / 5,000¥")).toBeDefined();
    expect(screen.queryByRole("button", { name: "返済する" })).toBeNull();
    expect(screen.getByRole("button", { name: "返済 5,000¥: 削除" })).toBeDefined();
  });
});
