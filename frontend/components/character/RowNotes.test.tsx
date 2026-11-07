import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import type { ComponentType } from "react";
import { describe, expect, it, vi } from "vitest";
import { QualityNotes, RowNotes } from "@/components/character/RowNotes";
import type { TabPanelProps } from "@/components/character/types";
import type { Updater } from "@/lib/character/patch-queue";
import type { Character } from "@/lib/types";
import { makeCharacter, panelProps, testUi } from "@/tests/fixtures";
import { ArmorGear } from "./tabs/gear/ArmorGear";
import { CommlinkGear } from "./tabs/gear/CommlinkGear";
import { LifestyleGear } from "./tabs/gear/LifestyleGear";
import { AppRows } from "./tabs/gear/AppRows";
import { GearChild } from "./tabs/gear/misc/GearChild";
import { QiFociSection } from "./tabs/adept/QiFociSection";

/** What a patch made of `updater` sends, read against `ch`. */
function sent(patch: ReturnType<typeof vi.fn>, ch: Character) {
  const body = patch.mock.calls.at(-1)![0];
  return typeof body === "function" ? (body as Updater)(ch) : body;
}

function type(box: HTMLElement, value: string) {
  fireEvent.change(box, { target: { value } });
  // `@testing-library/dom`'s blur does not reach React's onBlur
  fireEvent.focusOut(box);
}

describe("<RowNotes>", () => {
  const ch = makeCharacter({
    armor: [
      { id: "a1", armor_id: "x", notes: "", nickname: "" },
      { id: "a2", armor_id: "y", notes: "Patched twice", nickname: "Old Faithful" },
    ],
    spells: [{ id: "s1", spell_id: "z" }],
  } as never);

  it("is nothing for a row the character does not hold", () => {
    const { container } = render(
      <RowNotes ch={ch} bucket="armor" id="gone" of="Gone" ui={testUi} patch={() => {}} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("asks for the player's own name only where Chummer keeps one", () => {
    render(<RowNotes ch={ch} bucket="armor" id="a1" of="Coat" ui={testUi} patch={() => {}} />);
    render(<RowNotes ch={ch} bucket="spells" id="s1" of="Heal" ui={testUi} patch={() => {}} />);
    expect(screen.getByRole("textbox", { name: "Coat の呼び名" })).toBeDefined();
    expect(screen.getByRole("textbox", { name: "Coat の備考" })).toBeDefined();
    expect(screen.queryByRole("textbox", { name: "Heal の呼び名" })).toBeNull();
    expect(screen.getByRole("textbox", { name: "Heal の備考" })).toBeDefined();
  });

  it("is open from the start when something is written, and shows the name", () => {
    const { container } = render(
      <>
        <RowNotes ch={ch} bucket="armor" id="a1" of="Coat" ui={testUi} patch={() => {}} />
        <RowNotes ch={ch} bucket="armor" id="a2" of="Jacket" ui={testUi} patch={() => {}} />
      </>,
    );
    const [empty, written] = container.querySelectorAll("details");
    expect(empty.open).toBe(false);
    expect(written.open).toBe(true);
    expect(written.querySelector("summary")!.textContent).toBe("呼び名・備考：Old Faithful");
  });

  it("saves on leaving the box, only that row, against the character as saved", () => {
    const patch = vi.fn();
    render(<RowNotes ch={ch} bucket="armor" id="a2" of="Jacket" ui={testUi} patch={patch} />);
    const box = screen.getByRole("textbox", { name: "Jacket の備考" });
    fireEvent.change(box, { target: { value: "Patched three times\n" } });
    expect(patch).not.toHaveBeenCalled();
    expect((box as HTMLTextAreaElement).value).toBe("Patched three times\n");
    fireEvent.focusOut(box);
    // a rating changed since, which the updater must not undo
    const saved = { ...ch, armor: ch.armor!.map((row) => ({ ...row, rating: 3 })) };
    const rows = sent(patch, saved).armor as { id: string; notes: string; rating: number }[];
    expect(rows.map((row) => [row.id, row.notes, row.rating])).toEqual([
      ["a1", "", 3],
      ["a2", "Patched three times\n", 3],
    ]);
  });

  it("sends nothing when the text did not change", () => {
    const patch = vi.fn();
    render(<RowNotes ch={ch} bucket="armor" id="a2" of="Jacket" ui={testUi} patch={patch} />);
    fireEvent.focusOut(screen.getByRole("textbox", { name: "Jacket の呼び名" }));
    expect(patch).not.toHaveBeenCalled();
  });
});

describe("<QualityNotes>", () => {
  const ch = makeCharacter({ quality_notes: { q1: "Since the war", q2: "Keep" } } as never);

  it("keeps the note under the quality's key", () => {
    const patch = vi.fn();
    render(<QualityNotes ch={ch} noteKey="q1" of="Guts" ui={testUi} patch={patch} />);
    type(screen.getByRole("textbox", { name: "Guts の備考" }), "Since the bugs");
    expect(sent(patch, ch)).toEqual({ quality_notes: { q1: "Since the bugs", q2: "Keep" } });
  });

  it("drops the key once the note is cleared", () => {
    const patch = vi.fn();
    render(<QualityNotes ch={ch} noteKey="q1" of="Guts" ui={testUi} patch={patch} />);
    type(screen.getByRole("textbox", { name: "Guts の備考" }), "");
    expect(sent(patch, ch)).toEqual({ quality_notes: { q2: "Keep" } });
  });
});

/** Two owned rows, mirrored into `character` and `derived` under their keys. */
function owning(chKey: string, dKey: string, rows: Record<string, unknown>[]): Character {
  return makeCharacter({ [chKey]: rows, derived: { [dKey]: rows } } as never);
}

const PANELS: [string, ComponentType<never>, string, string, Record<string, unknown>][] = [
  [
    "ArmorGear",
    ArmorGear,
    "armor",
    "armor_items",
    { armor_value: 9, contributes: 9, equipped: true, rating: 1, rating_max: 0, mods: [] },
  ],
  [
    "CommlinkGear",
    CommlinkGear,
    "commlinks",
    "commlinks",
    { rating: 1, rating_max: 6, device_rating: 1, dataprocessing: 1, firewall: 1, programs: 0 },
  ],
  [
    "LifestyleGear",
    LifestyleGear,
    "lifestyles",
    "lifestyles",
    { months: 1, monthly: 100, qualities: [] },
  ],
];

describe.each(PANELS)("<%s> notes", (_name, Panel, chKey, dKey, fields) => {
  const row = (id: string, name: string) => ({
    id,
    name,
    nuyen: 100,
    source: "SR5",
    category: "",
    ...fields,
  });

  it("gives each owned row its own box, and saves the second without the first", () => {
    const ch = owning(chKey, dKey, [row("x1", "First"), row("x2", "Second")]);
    const patch = vi.fn();
    const P = Panel as ComponentType<TabPanelProps>;
    render(<P {...panelProps(ch, { patch })} />);
    expect(screen.getByRole("textbox", { name: "First の備考" })).toBeDefined();
    type(screen.getByRole("textbox", { name: "Second の備考" }), "Under the floorboards");
    const rows = sent(patch, ch)[chKey] as { id: string; notes?: string }[];
    expect(rows.map((r) => [r.id, r.notes])).toEqual([
      ["x1", undefined],
      ["x2", "Under the floorboards"],
    ]);
  });
});

describe("notes on what is put inside other gear", () => {
  const derivedRow = (id: string, name: string, parent_id: string | null) => ({
    id,
    gear_id: `g-${id}`,
    name,
    parent_id,
    nuyen: 10,
    rating: 1,
    rating_max: 0,
    qty: 1,
    included: false,
  });

  it("gives each thing in a container its own box, as deep as it nests", () => {
    const rows = [
      derivedRow("clip", "Spare Clip", null),
      derivedRow("darts", "Injection Darts", "clip"),
      derivedRow("drug", "Narcoject", "darts"),
    ];
    const ch = makeCharacter({ gear: rows, derived: { gear: rows } } as never);
    const patch = vi.fn();
    render(
      <GearChild
        child={rows[1] as never}
        all={rows as never}
        ch={ch}
        tr={(s) => s}
        ui={testUi}
        patch={patch}
      />,
    );
    expect(screen.getByRole("textbox", { name: "Injection Darts の呼び名" })).toBeDefined();
    type(screen.getByRole("textbox", { name: "Narcoject の備考" }), "Two left");
    const sentRows = sent(patch, ch).gear as { id: string; notes?: string }[];
    expect(sentRows.map((r) => [r.id, r.notes])).toEqual([
      ["clip", undefined],
      ["darts", undefined],
      ["drug", "Two left"],
    ]);
  });

  it("keeps an app's note and name on the app", () => {
    const apps = [derivedRow("a1", "Diagnostics", "link"), derivedRow("a2", "Ticker", "link")];
    const ch = makeCharacter({ apps, derived: { apps } } as never);
    const patch = vi.fn();
    render(<AppRows hostId="link" hostName="Meta Link" {...panelProps(ch, { patch })} />);
    type(screen.getByRole("textbox", { name: "Ticker の呼び名" }), "News");
    const sentRows = sent(patch, ch).apps as { id: string; nickname?: string }[];
    expect(sentRows.map((r) => [r.id, r.nickname])).toEqual([
      ["a1", undefined],
      ["a2", "News"],
    ]);
  });

  it("keeps a Qi focus's note and name on the focus", () => {
    const own = [{ id: "q1", rating: 2, power_id: "p", bonded: true, nickname: "Beads" }];
    const shown = [
      {
        ...own[0],
        name: "Combat Sense",
        nuyen: 6000,
        karma: 4,
        power_rating: 1,
        power_rating_max: 1,
        rating_min: 1,
        rating_max: 6,
        options: [],
      },
    ];
    const ch = makeCharacter({ qi_foci: own, derived: { qi_foci: shown } } as never);
    const patch = vi.fn();
    const { container } = render(<QiFociSection {...panelProps(ch, { patch })} />);
    // something is written: open from the start
    expect(container.querySelector("details")!.open).toBe(true);
    type(screen.getByRole("textbox", { name: "氣収束具: Combat Sense の備考" }), "From my teacher");
    expect(sent(patch, ch).qi_foci).toEqual([{ ...own[0], notes: "From my teacher" }]);
  });
});
