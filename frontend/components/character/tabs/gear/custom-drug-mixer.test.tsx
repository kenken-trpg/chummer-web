import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { CustomDrugMixer } from "./CustomDrugMixer";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * The mixer holds no state of its own beyond which component is selected: the
 * drug is patched as it is built, and every number on screen is the engine's
 * answer. So what these tests pin is the patch each control sends — a drug
 * edited by id would be the bug worth catching, because a drug that was just
 * mixed has no id until the server hands one back.
 */

const component = (id: string, name: string, category: string, levels = 1) => ({
  id,
  name,
  category,
  cost: "20",
  avail: "+1",
  addiction_rating: 0,
  addiction_threshold: 0,
  limit: 0,
  levels: Array.from({ length: levels }, (_, level) => ({
    level,
    effect: [],
    crash_damage: 0,
    speed: 0,
    duration: 0,
    info: "",
  })),
});

const CATALOG = makeCatalog({
  drug_components: [
    component("c-tank", "Tank", "Foundation"),
    component("c-crush", "Crush", "Block", 3),
  ],
  drug_component_grades: [
    { id: "g-std", name: "Standard", cost_multiplier: 1, addiction_threshold: 0 },
    { id: "g-street", name: "Street Cooked", cost_multiplier: 0.5, addiction_threshold: 0 },
  ],
} as any);

function renderMixer(ch: Character, patch: (b: Record<string, unknown>) => void) {
  return render(
    <CustomDrugMixer
      catalog={CATALOG}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
    />,
  );
}

/** A character holding the given mixed drugs, mirrored into `derived`. */
function mixing(drugs: Record<string, unknown>[], rows: Record<string, unknown>[] = []): Character {
  return makeCharacter({
    custom_drugs: drugs,
    derived: { custom_drugs: rows },
  } as any);
}

const drugRow = (id: string, over: Record<string, unknown> = {}) => ({
  id,
  name: "Wrecker",
  grade: "Standard",
  qty: 1,
  active: false,
  nuyen: 95,
  avail: "5R",
  addiction_rating: 6,
  addiction_threshold: 2,
  crash_damage: 2,
  speed: 9,
  duration: 0,
  infos: [],
  components: [{ component_id: "c-tank", name: "Tank", category: "Foundation", level: 0 }],
  effect: [],
  ...over,
});

describe("<CustomDrugMixer>", () => {
  it("starts a new drug with no components", () => {
    const patch = vi.fn();
    renderMixer(mixing([]), patch);

    fireEvent.click(screen.getByRole("button", { name: "調合ドラッグを作る" }));

    expect(patch.mock.calls[0][0]).toEqual({
      custom_drugs: [{ name: "", grade: "Standard", qty: 1, parts: [] }],
    });
  });

  it("adds the component at the level the option names", () => {
    const patch = vi.fn();
    renderMixer(mixing([{ id: "d1", name: "Wrecker", parts: [] }], [drugRow("d1")]), patch);

    fireEvent.change(screen.getByLabelText(/コンポーネントを足す/), {
      target: { value: "c-crush@2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "追加" }));

    expect(patch.mock.calls[0][0]).toEqual({
      custom_drugs: [{ id: "d1", name: "Wrecker", parts: [{ component_id: "c-crush", level: 2 }] }],
    });
  });

  it("edits the drug at its position, so an id-less new drug is still editable", () => {
    // Two drugs the server has not seen yet: matching on `id` would rename both
    const patch = vi.fn();
    renderMixer(
      mixing([
        { name: "", grade: "Standard", qty: 1, parts: [] },
        { name: "", grade: "Standard", qty: 1, parts: [] },
      ]),
      patch,
    );

    fireEvent.change(screen.getAllByLabelText("ドラッグ名")[1], { target: { value: "Wrecker" } });

    const body = patch.mock.calls[0][0].custom_drugs as { name: string }[];
    expect(body.map((drug) => drug.name)).toEqual(["", "Wrecker"]);
  });

  it("shows the engine's totals for the drug, not its own arithmetic", () => {
    renderMixer(mixing([{ id: "d1", name: "Wrecker", parts: [] }], [drugRow("d1")]), vi.fn());

    expect(screen.getByText(/95¥/)).toBeTruthy();
    expect(screen.getByText(/入手 5R/)).toBeTruthy();
    expect(screen.getByText(/中毒 R6\/閾値2/)).toBeTruthy();
    expect(screen.getByText(/クラッシュ 2S/)).toBeTruthy();
  });

  it("removes one component without touching the rest of the mix", () => {
    const patch = vi.fn();
    renderMixer(
      mixing(
        [
          {
            id: "d1",
            name: "Wrecker",
            parts: [
              { component_id: "c-tank", level: 0 },
              { component_id: "c-crush", level: 1 },
            ],
          },
        ],
        [drugRow("d1")],
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);

    const body = patch.mock.calls[0][0].custom_drugs as { parts: { component_id: string }[] }[];
    expect(body[0].parts.map((part) => part.component_id)).toEqual(["c-crush"]);
  });
});
