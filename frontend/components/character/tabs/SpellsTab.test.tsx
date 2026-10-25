import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SpellsTab } from "@/components/character/tabs/SpellsTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const fireball = {
  id: "fb",
  name: "Fireball",
  category: "Combat",
  dv: "F-3",
  kind: "spell",
  source: "SR5",
};
const rite = {
  id: "rite",
  name: "Circle of Healing",
  category: "Health",
  dv: "F-2",
  kind: "ritual",
  source: "SR5",
};
const increase = {
  id: "inc",
  name: "Increase [Attribute]",
  category: "Health",
  dv: "F-3",
  kind: "spell",
  source: "SR5",
  needs_extra: true,
};
const wall = {
  id: "wall",
  name: "[Element] Wall",
  category: "Manipulation",
  dv: "F-2",
  kind: "spell",
  source: "SG",
  needs_extra: true,
};
const attributes = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"];

/** A learned spell's row, as `resolve_spells` writes it. */
function learned(over: Record<string, unknown>) {
  return { dv: "F-3", free: true, karma: 0, kind: "spell", ...over };
}

const traditions = [{ id: "hermetic", name: "Hermetic", drain_attrs: ["WIL", "LOG"] }];

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
    t?: (key: string, fallback?: string) => string;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <SpellsTab
      {...panelProps(ch, { patch: over.patch ?? (() => {}), ...(over.t ? { t: over.t } : {}) })}
      catalog={
        over.catalog ??
        makeCatalog({ spells: [fireball, rite] as never, traditions: traditions as never })
      }
    />,
  );
}

describe("<SpellsTab>", () => {
  it("renders the free-slot line, tradition select and kind tabs", () => {
    renderTab();
    expect(screen.getByText(/無料 0\/0/)).toBeDefined();
    expect(screen.getByRole("combobox")).toBeDefined();
    for (const label of ["すべて", "呪文", "儀式", "エンチャント"]) {
      expect(screen.getByRole("button", { name: label })).toBeDefined();
    }
  });

  it("explains where the free spells come from and what the rest cost", () => {
    renderTab();
    expect(screen.getByRole("button", { name: "呪文の無料枠 の説明" })).toBeDefined();
    expect(screen.getByText(/魔法の欄で選んだタレントの呪文数/)).toBeDefined();
    expect(screen.getByText(/接触射程の呪文にしか使えない枠/)).toBeDefined();
    expect(screen.getByText(/1 つずつカルマで買う/)).toBeDefined();
  });

  it("sets the tradition through patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "hermetic" } });
    expect(patch).toHaveBeenCalledWith({ tradition_id: "hermetic" });
  });

  it("adds a spell from the catalog via patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Fireball"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ spells: [{ spell_id: "fb" }] });
  });

  it("filters the catalog by the kind tabs", () => {
    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "儀式" }));
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Circle of Healing"]);
  });

  it("picks the attribute of a spell that names one, and shows it in the name", () => {
    const patch = vi.fn();
    const names: Record<string, string> = { String_AttributeWILLong: "意志力" };
    renderTab({
      patch,
      t: (key, fallback) => names[key] ?? fallback ?? key,
      character: {
        spells: [{ id: "s1", spell_id: "inc", extra: "WIL" }],
        derived: {
          spells: [
            learned({
              id: "s1",
              spell_id: "inc",
              name: "Increase [Attribute]",
              extra: "WIL",
              extra_kind: "attribute",
              extra_options: attributes,
            }),
          ] as never,
        },
      },
      catalog: makeCatalog({ spells: [increase] as never, traditions: traditions as never }),
    });
    const row = document.querySelector(".cyber-item")!;
    expect(row.querySelector("b")!.textContent).toBe("Increase [Attribute] (意志力)");
    const select = screen.getByRole("combobox", { name: "能力値" }) as HTMLSelectElement;
    expect(select.value).toBe("WIL");
    expect(select.options).toHaveLength(attributes.length + 1);
    fireEvent.change(select, { target: { value: "CHA" } });
    expect(patch).toHaveBeenCalledWith({ spells: [{ id: "s1", spell_id: "inc", extra: "CHA" }] });
    // the "?" says each pick is a spell of its own
    expect(screen.getByRole("button", { name: "能力値 の説明" })).toBeDefined();
    expect(screen.getByText(/選んだ能力値ごとに 1 つの呪文として数える/)).toBeDefined();
    expect(screen.getByText(/重複として外れる/)).toBeDefined();
  });

  it("keeps a spell that picks on offer after it is learned, and only that one", () => {
    renderTab({
      character: {
        spells: [
          { id: "s1", spell_id: "inc", extra: "WIL" },
          { id: "s2", spell_id: "fb" },
        ],
      },
      catalog: makeCatalog({
        spells: [fireball, increase] as never,
        traditions: traditions as never,
      }),
    });
    const offered = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(offered).toEqual(["Increase [Attribute]"]);
  });

  it("commits a typed pick when the field is left", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        spells: [{ id: "s1", spell_id: "wall" }],
        derived: {
          spells: [
            learned({
              id: "s1",
              spell_id: "wall",
              name: "[Element] Wall",
              extra: "",
              extra_kind: "text",
            }),
          ] as never,
        },
      },
      catalog: makeCatalog({ spells: [wall] as never, traditions: traditions as never }),
    });
    const input = screen.getByRole("textbox", { name: "対象" });
    fireEvent.change(input, { target: { value: " Ice " } });
    expect(patch).not.toHaveBeenCalled();
    fireEvent.focusOut(input);
    expect(patch).toHaveBeenCalledWith({ spells: [{ id: "s1", spell_id: "wall", extra: "Ice" }] });
    expect(screen.getByRole("button", { name: "対象 の説明" })).toBeDefined();
    expect(screen.getByText(/［ ］に入るもの/)).toBeDefined();
  });
});
