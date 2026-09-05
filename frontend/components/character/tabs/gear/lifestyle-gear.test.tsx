import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { LifestyleGear } from "./LifestyleGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * The one panel whose owned rows are edited through the *character* rather
 * than the derived payload.
 *
 * A lifestyle's qualities live in two fields on `ch.lifestyles[n]` —
 * `quality_ids`, a list that may hold the same id twice, and
 * `quality_extras`, a map keyed by that id. The row on screen comes from
 * `d.lifestyles`, which has already merged in the free grids the lifestyle
 * comes with. So every control here has to find its way back to the raw row
 * (`raw`) before it can edit anything, and a control that patches the derived
 * shape instead writes a lifestyle the engine will not recognise.
 *
 * Two consequences are pinned below: removing a quality taken twice removes
 * *one* of them and keeps its target, and a quality that came with the
 * lifestyle has no remove button at all.
 */

const lifestyle = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  lifestyle_id: `c-${id}`,
  monthly: 5000,
  base_monthly: 5000,
  months: 1,
  increment: "month",
  nuyen: 5000,
  source: "SR5",
  qualities: [],
  ...over,
});

const quality = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  quality_id: `cq-${id}`,
  lp: 1,
  cost: 0,
  multiplier: 0,
  free: false,
  from_freegrid: false,
  ...over,
});

function renderLifestyles(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog = makeCatalog(),
) {
  return render(
    <LifestyleGear
      catalog={catalog}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
    />,
  );
}

/**
 * `raw` is the character's own row and `derived` the merged one. They are
 * separate arguments here because the difference is the point.
 */
function owning(raw: Record<string, unknown>[], derived: Record<string, unknown>[]): Character {
  return makeCharacter({ lifestyles: raw, derived: { lifestyles: derived } } as any);
}

describe("<LifestyleGear> the cost line", () => {
  it("spells out how the monthly figure was reached", () => {
    const { container } = renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 3, quality_ids: [] }],
        [
          lifestyle("l1", "Middle", {
            base_monthly: 5000,
            multiplier_pct: 20,
            quality_monthly: 500,
            monthly: 6500,
            months: 3,
            nuyen: 19500,
            lp_used: 2,
            lp_max: 3,
          }),
        ],
      ),
      vi.fn(),
    );

    expect(container.textContent).toContain("基本 5,000¥");
    expect(container.textContent).toContain("倍率 +20%");
    expect(container.textContent).toContain("品質 +500¥");
    expect(container.textContent).toContain("6,500¥/ヶ月 × 3 = 19,500¥");
    expect(container.textContent).toContain("LP 2/3");
  });

  it("leaves out the parts that are zero", () => {
    const { container } = renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: [] }],
        [lifestyle("l1", "Low", { multiplier_pct: 0, quality_monthly: 0 })],
      ),
      vi.fn(),
    );

    expect(container.textContent).not.toContain("倍率");
    expect(container.textContent).not.toContain("品質 +");
    expect(container.textContent).not.toContain("LP ");
  });

  it("labels the count with the lifestyle's own increment", () => {
    const { container } = renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 2, quality_ids: [] }],
        [lifestyle("l1", "Hospitalized", { increment: "day", months: 2 })],
      ),
      vi.fn(),
    );

    // a hospital stay is billed by the day; calling that box "月" is wrong
    expect(screen.getByLabelText("日")).toBeDefined();
    expect(container.textContent).toContain("¥/日");
  });

  it("changes the count on the row that moved, not both", () => {
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          { id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: [] },
          { id: "l2", lifestyle_id: "c-l2", months: 1, quality_ids: [] },
        ],
        [lifestyle("l1", "Low"), lifestyle("l2", "Middle")],
      ),
      patch,
    );

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "6" } });

    const rows = patch.mock.calls[0][0].lifestyles as { id: string; months: number }[];
    expect(rows.find((r) => r.id === "l1")?.months).toBe(1);
    expect(rows.find((r) => r.id === "l2")?.months).toBe(6);
  });

  it("deletes one lifestyle and keeps the other", () => {
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          { id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: [] },
          { id: "l2", lifestyle_id: "c-l2", months: 1, quality_ids: [] },
        ],
        [lifestyle("l1", "Low"), lifestyle("l2", "Middle")],
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    expect((patch.mock.calls[0][0].lifestyles as { id: string }[]).map((r) => r.id)).toEqual([
      "l2",
    ]);
  });
});

describe("<LifestyleGear> the qualities on a lifestyle", () => {
  it("prints LP, surcharge, multiplier and target for each one", () => {
    const { container } = renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: ["cq-q1"] }],
        [
          lifestyle("l1", "Middle", {
            qualities: [
              quality("q1", "Special Work Area", {
                lp: 2,
                cost: 1000,
                multiplier: 10,
                extra: "Alchemy",
              }),
            ],
          }),
        ],
      ),
      vi.fn(),
    );

    expect(container.textContent).toContain("Special Work Area（Alchemy）");
    expect(container.textContent).toContain("LP 2");
    expect(container.textContent).toContain("+1,000¥");
    expect(container.textContent).toContain("+10%");
  });

  it("says free rather than showing a zero surcharge", () => {
    const { container } = renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: ["cq-q1"] }],
        [
          lifestyle("l1", "Middle", {
            qualities: [quality("q1", "Cramped", { free: true, cost: 500 })],
          }),
        ],
      ),
      vi.fn(),
    );

    expect(container.textContent).toContain("無料");
    expect(container.textContent).not.toContain("+500¥");
  });

  it("a quality that came with the lifestyle cannot be removed", () => {
    // free grids are part of what you bought; they are not yours to drop
    renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: [] }],
        [
          lifestyle("l1", "Middle", {
            qualities: [quality("q1", "Local Grid", { from_freegrid: true })],
          }),
        ],
      ),
      vi.fn(),
    );

    expect(screen.queryByRole("button", { name: "外す" })).toBeNull();
    expect(screen.getByText(/付属|同梱/)).toBeDefined();
  });

  it("removing a quality taken twice removes one of them and keeps its target", () => {
    // `quality_ids` is a list, not a set: dropping every copy and its target
    // would silently undo the second purchase as well
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          {
            id: "l1",
            lifestyle_id: "c-l1",
            months: 1,
            quality_ids: ["cq-q1", "cq-q1", "cq-q2"],
            quality_extras: { "cq-q1": "Alchemy", "cq-q2": "Garage" },
          },
        ],
        [
          lifestyle("l1", "Middle", {
            qualities: [
              quality("q1a", "Special Work Area", { quality_id: "cq-q1" }),
              quality("q1b", "Special Work Area", { quality_id: "cq-q1" }),
              quality("q2", "Extra Space", { quality_id: "cq-q2" }),
            ],
          }),
        ],
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);

    const row = (patch.mock.calls[0][0].lifestyles as Record<string, any>[])[0];
    expect(row.quality_ids).toEqual(["cq-q1", "cq-q2"]);
    expect(row.quality_extras).toEqual({ "cq-q1": "Alchemy", "cq-q2": "Garage" });
  });

  it("removing the last copy of a quality drops its target too", () => {
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          {
            id: "l1",
            lifestyle_id: "c-l1",
            months: 1,
            quality_ids: ["cq-q1", "cq-q2"],
            quality_extras: { "cq-q1": "Alchemy", "cq-q2": "Garage" },
          },
        ],
        [
          lifestyle("l1", "Middle", {
            qualities: [
              quality("q1", "Special Work Area", { quality_id: "cq-q1" }),
              quality("q2", "Extra Space", { quality_id: "cq-q2" }),
            ],
          }),
        ],
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);

    const row = (patch.mock.calls[0][0].lifestyles as Record<string, any>[])[0];
    expect(row.quality_ids).toEqual(["cq-q2"]);
    // a target left behind would be re-applied if the quality is bought again
    expect(row.quality_extras).toEqual({ "cq-q2": "Garage" });
  });

  it("edits the target of a quality without disturbing the other targets", () => {
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          {
            id: "l1",
            lifestyle_id: "c-l1",
            months: 1,
            quality_ids: ["cq-q1", "cq-q2"],
            quality_extras: { "cq-q2": "Garage" },
          },
        ],
        [
          lifestyle("l1", "Middle", {
            qualities: [
              quality("q1", "Special Work Area", { quality_id: "cq-q1", needs_extra: true }),
              quality("q2", "Extra Space", { quality_id: "cq-q2" }),
            ],
          }),
        ],
      ),
      patch,
    );

    fireEvent.change(screen.getByPlaceholderText("対象"), { target: { value: "Alchemy" } });

    const row = (patch.mock.calls[0][0].lifestyles as Record<string, any>[])[0];
    expect(row.quality_extras).toEqual({ "cq-q1": "Alchemy", "cq-q2": "Garage" });
  });

  it("edits the lifestyle it belongs to and leaves the other one alone", () => {
    // both rows render the same controls; a map without the id check writes
    // the second lifestyle's qualities over the first one's
    const patch = vi.fn();
    renderLifestyles(
      owning(
        [
          { id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: ["cq-a"] },
          { id: "l2", lifestyle_id: "c-l2", months: 1, quality_ids: ["cq-b"] },
        ],
        [
          lifestyle("l1", "Low", {
            qualities: [quality("qa", "Cramped", { quality_id: "cq-a" })],
          }),
          lifestyle("l2", "Middle", {
            qualities: [quality("qb", "Extra Space", { quality_id: "cq-b" })],
          }),
        ],
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    const rows = patch.mock.calls[0][0].lifestyles as Record<string, any>[];
    expect(rows.find((r) => r.id === "l1")!.quality_ids).toEqual(["cq-a"]);
    expect(rows.find((r) => r.id === "l2")!.quality_ids).toEqual([]);
  });

  it("gives a free-grid quality no target box even when it wants one", () => {
    renderLifestyles(
      owning(
        [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: [] }],
        [
          lifestyle("l1", "Middle", {
            qualities: [quality("q1", "Local Grid", { from_freegrid: true, needs_extra: true })],
          }),
        ],
      ),
      vi.fn(),
    );

    expect(screen.queryByPlaceholderText("対象")).toBeNull();
  });
});

describe("<LifestyleGear> the quality picker", () => {
  const catalog = () =>
    makeCatalog({
      lifestyle_qualities: [
        { id: "cq-work", name: "Special Work Area", lp: 2, cost: 0, source: "SR5" },
        { id: "cq-space", name: "Extra Space", lp: 1, cost: 0, source: "RF" },
        // taken already, and not repeatable
        { id: "cq-cramped", name: "Cramped", lp: -1, cost: 0, source: "SR5" },
        // only offered on the lifestyles it names
        { id: "cq-vault", name: "Vault", lp: 3, cost: 0, source: "SR5", allowed: ["High"] },
        // a supplement quality that is free and so stays off the list
        { id: "cq-sg", name: "Obscure Perk", lp: 0, cost: 0, source: "SG" },
      ],
    } as any);

  const middle = (over: Record<string, unknown> = {}) =>
    owning(
      [{ id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: ["cq-cramped"], ...over }],
      [
        lifestyle("l1", "Middle", {
          qualities: [quality("q1", "Cramped", { quality_id: "cq-cramped" })],
        }),
      ],
    );

  it("hides what is taken, what this lifestyle cannot have, and free supplements", () => {
    renderLifestyles(middle(), vi.fn(), catalog());

    const select = screen.getByRole("combobox", { name: "Middle: ライフスタイル品質" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual([
      "ライフスタイル品質",
      "Special Work Area (LP 2)",
      "Extra Space (LP 1)",
    ]);
  });

  it("keeps offering a quality that may be taken more than once", () => {
    const repeatable = makeCatalog({
      lifestyle_qualities: [
        { id: "cq-cramped", name: "Cramped", lp: -1, cost: 0, source: "SR5", allow_multiple: true },
      ],
    } as any);
    renderLifestyles(middle(), vi.fn(), repeatable);

    const select = screen.getByRole("combobox", { name: "Middle: ライフスタイル品質" });
    expect([...select.querySelectorAll("option")]).toHaveLength(2); // prompt + Cramped
  });

  it("appends the chosen quality to that lifestyle only", () => {
    const patch = vi.fn();
    renderLifestyles(
      makeCharacter({
        lifestyles: [
          { id: "l0", lifestyle_id: "c-l0", months: 1, quality_ids: [] },
          { id: "l1", lifestyle_id: "c-l1", months: 1, quality_ids: ["cq-cramped"] },
        ],
        derived: {
          lifestyles: [
            lifestyle("l0", "Low"),
            lifestyle("l1", "Middle", {
              qualities: [quality("q1", "Cramped", { quality_id: "cq-cramped" })],
            }),
          ],
        },
      } as any),
      patch,
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Middle: ライフスタイル品質" });
    fireEvent.change(select, { target: { value: "cq-work" } });
    fireEvent.click(screen.getByRole("button", { name: "Middle: 追加" }));

    const rows = patch.mock.calls[0][0].lifestyles as Record<string, any>[];
    expect(rows.find((r) => r.id === "l1")!.quality_ids).toEqual(["cq-cramped", "cq-work"]);
    expect(rows.find((r) => r.id === "l0")!.quality_ids).toEqual([]);
  });

  it("carries a target typed alongside the quality into the patch", () => {
    const needsExtra = makeCatalog({
      lifestyle_qualities: [
        {
          id: "cq-work",
          name: "Special Work Area",
          lp: 2,
          cost: 0,
          source: "SR5",
          needs_extra: true,
        },
      ],
    } as any);
    const patch = vi.fn();
    renderLifestyles(middle({ quality_ids: [] }), patch, needsExtra);

    fireEvent.change(screen.getByRole("combobox", { name: "Middle: ライフスタイル品質" }), {
      target: { value: "cq-work" },
    });
    // an <input list=…> is a combobox, not a textbox
    fireEvent.change(screen.getByRole("combobox", { name: "Middle: 対象" }), {
      target: { value: "Alchemy" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Middle: 追加" }));

    const row = (patch.mock.calls[0][0].lifestyles as Record<string, any>[])[0];
    expect(row.quality_ids).toEqual(["cq-work"]);
    expect(row.quality_extras).toEqual({ "cq-work": "Alchemy" });
  });

  it("shows no picker at all when nothing is on offer", () => {
    renderLifestyles(middle(), vi.fn(), makeCatalog());
    expect(screen.queryByRole("combobox")).toBeNull();
  });
});

describe("<LifestyleGear> buying a lifestyle", () => {
  const catalog = () =>
    makeCatalog({
      lifestyles: [
        { id: "c-low", name: "Low", cost: 2000, increment: "month", lp: 3, source: "SR5" },
        {
          id: "c-hos",
          name: "Hospitalized",
          cost: 500,
          increment: "day",
          lp: 0,
          source: "SG",
          freegrids: ["Local Grid"],
        },
      ],
    } as any);
  const offered = () =>
    [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

  it("lists the core lifestyles until the search box has something in it", () => {
    renderLifestyles(owning([], []), vi.fn(), catalog());
    expect(offered()).toEqual(["Low"]);

    fireEvent.change(screen.getByPlaceholderText("ライフスタイルを検索"), {
      target: { value: "hosp" },
    });
    expect(offered()).toEqual(["Hospitalized"]);
  });

  it("describes a lifestyle by its increment, LP and free grids", () => {
    renderLifestyles(owning([], []), vi.fn(), catalog());
    fireEvent.change(screen.getByPlaceholderText("ライフスタイルを検索"), {
      target: { value: "hosp" },
    });

    const row = document.querySelector(".quality-list .quality-item") as HTMLElement;
    expect(within(row).getByText(/500¥\/日/)).toBeDefined();
    expect(row.textContent).toContain("付属グリッド 1");
  });

  it("buys one month of it, with no qualities yet", () => {
    const patch = vi.fn();
    renderLifestyles(owning([], []), patch, catalog());

    fireEvent.click(screen.getByRole("button", { name: /Low/ }));

    expect(patch.mock.calls[0][0].lifestyles).toEqual([
      { lifestyle_id: "c-low", months: 1, quality_ids: [] },
    ]);
  });
});
