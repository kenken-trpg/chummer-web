/**
 * The career sidebar's reward log: the one place a run's karma and nuyen are
 * entered, and the one place they can be taken back out. It is rendered by
 * `<CharacterSidebar>`'s tests but nothing drove it — so the rules that keep a
 * log honest (no empty rows, no negatives, every surviving row rewritten in
 * the stored shape) were untested.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { SidebarCareerRewards } from "@/components/character/sidebar/SidebarCareerRewards";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import type { Character } from "@/lib/types";

type Patch = (body: Record<string, unknown>) => void;

function renderBlock(
  over: { derived?: Record<string, unknown>; career?: boolean; patch?: Patch | null } = {},
) {
  const ch = makeCharacter({ career: true, derived: over.derived } as never);
  return render(
    <SidebarCareerRewards
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

const karmaField = () => screen.getByRole("spinbutton", { name: "カルマ" });
const nuyenField = () => screen.getByRole("spinbutton", { name: "新円" });
const addButton = () => screen.getByRole("button", { name: "報酬を追加" });

describe("<SidebarCareerRewards>", () => {
  // In creation mode there is nothing to log, and without `patch` nothing
  // could be written anyway — both hide the panel rather than show a dead one.
  it("appears only in career mode, and only when it can write", () => {
    const { container, unmount } = renderBlock({ career: false });
    expect(container.textContent).toBe("");
    unmount();

    const readOnly = renderBlock({ patch: null });
    expect(readOnly.container.textContent).toBe("");

    // and it is there when both hold
    readOnly.unmount();
    expect(renderBlock().container.querySelector(".career-panel")).not.toBeNull();
  });

  it("adds a reward and clears the fields it was typed into", () => {
    const patch = vi.fn();
    renderBlock({ patch });

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "  Milk run  " } });
    fireEvent.change(karmaField(), { target: { value: "5" } });
    fireEvent.change(nuyenField(), { target: { value: "4000" } });
    fireEvent.click(addButton());

    expect(patch).toHaveBeenCalledWith({
      reward_log: [{ id: expect.any(String), label: "Milk run", karma: 5, nuyen: 4000 }],
    });
    expect((screen.getByRole("textbox") as HTMLInputElement).value).toBe("");
    expect((karmaField() as HTMLInputElement).value).toBe("0");
    expect((nuyenField() as HTMLInputElement).value).toBe("0");
  });

  it("will not log a reward that is worth nothing", () => {
    const patch = vi.fn();
    renderBlock({ patch });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "A favour" } });
    fireEvent.click(addButton());
    expect(patch).not.toHaveBeenCalled();
  });

  it("refuses to take karma or nuyen away through a reward", () => {
    const patch = vi.fn();
    renderBlock({ patch });
    fireEvent.change(karmaField(), { target: { value: "-5" } });
    fireEvent.change(nuyenField(), { target: { value: "-1000" } });
    expect((karmaField() as HTMLInputElement).value).toBe("0");
    fireEvent.click(addButton());
    expect(patch).not.toHaveBeenCalled();
  });

  // The rows that survive a delete are written back too, so whatever shape a
  // save arrived in, what leaves here is the stored one.
  it("deletes one row and rewrites the rest in the stored shape", () => {
    const patch = vi.fn();
    renderBlock({
      patch,
      derived: {
        reward_log: [
          { id: "r1", label: "Milk run", karma: 5, nuyen: 4000 },
          // a save can carry a negative or a string here; neither survives
          { id: "r2", label: "", karma: -3, nuyen: "4000", extra: "not stored" },
        ],
      },
    });

    // an unnamed row reads as 報酬 in the reader's language, not as blank
    expect(screen.getByText(/報酬 · -3K/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Milk run: 削除" }));
    expect(patch).toHaveBeenCalledWith({
      reward_log: [{ id: "r2", label: "", karma: 0, nuyen: 4000 }],
    });
  });

  it("shows the totals the engine worked out, not the log's own sum", () => {
    renderBlock({
      derived: {
        karma_earned: 12,
        nuyen_earned: 15000,
        reward_log: [{ id: "r1", label: "Milk run", karma: 5, nuyen: 4000 }],
      },
    });
    expect(screen.getByText("12K / 15,000¥")).toBeDefined();
  });

  // A Chummer save can arrive with totals this app cannot explain from the
  // log; they are shown as one adjustment and can be dropped in one go.
  it("offers the Chummer adjustment as a single row to clear", () => {
    const patch = vi.fn();
    renderBlock({ patch, derived: { karma_adjust: 7, nuyen_adjust: 2500 } });

    expect(screen.getByText(/Chummer との差 · 7K \/ 2,500¥/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Chummer との差: 削除" }));
    expect(patch).toHaveBeenCalledWith({ karma_adjust: 0, nuyen_adjust: 0 });
  });

  it("hides the adjustment row when there is nothing to reconcile", () => {
    renderBlock({ derived: { karma_adjust: 0, nuyen_adjust: 0 } });
    expect(screen.queryByText(/Chummer との差/)).toBeNull();
  });

  it("folds the breakdown away, and says なし for a side that has none", () => {
    renderBlock({
      derived: {
        karma_spend_breakdown: [{ notice: { key: "engine.spend.qualities" }, amount: 4 }],
        nuyen_spend_breakdown: [],
      },
    });
    expect(screen.queryByText("カルマ消費")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "成長／買い物の内訳" }));
    expect(screen.getByText("カルマ消費")).toBeDefined();
    expect(screen.getByText("4K")).toBeDefined();
    expect(screen.getByText("なし")).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: "内訳を隠す" }));
    expect(screen.queryByText("カルマ消費")).toBeNull();
  });

  it("lists what a Chummer save already spent, without counting it again", () => {
    renderBlock({
      derived: {
        expense_log: [
          { id: "e1", label: "Initiation", karma: 13, nuyen: 0 },
          { id: "e2", label: "", karma: 0, nuyen: 2000 },
          { id: "e3", label: "Both", karma: 2, nuyen: 500 },
        ],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "成長／買い物の内訳" }));

    expect(screen.getByText("Chummer での支出")).toBeDefined();
    expect(screen.getByText("13K")).toBeDefined();
    expect(screen.getByText("支出").nextSibling?.textContent).toBe("2,000¥");
    expect(screen.getByText("Both").nextSibling?.textContent).toBe("2K / 500¥");
  });
});
