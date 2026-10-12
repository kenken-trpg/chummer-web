/**
 * The technomancer's half of the summoning tabs. `<SpiritsTab>` has had a test
 * since it was written; this one had none, and the two are not the same shape:
 * a sprite is compiled or registered rather than bound, its services are tasks
 * that a reboot ends, and every control writes through `patch` onto the saved
 * rows — not the derived ones it is rendered from.
 */
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SpritesTab } from "@/components/character/tabs/SpritesTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const catalogSprites = [
  { id: "courier", name: "Courier Sprite", source: "SR5" },
  { id: "crack", name: "Crack Sprite", source: "SR5" },
];

/** One owned sprite, as the engine hands it back. */
const owned = (over: Record<string, unknown> = {}) => ({
  id: "s1",
  sprite_id: "courier",
  name: "Courier Sprite",
  level: 3,
  level_max: 6,
  services: 2,
  registered: false,
  hits: null,
  opposed_hits: null,
  source: "SR5",
  ...over,
});

function renderTab(
  over: {
    sprites?: Record<string, unknown>[];
    derived?: Record<string, unknown>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter({
    sprites: over.sprites,
    derived: { sprites: over.sprites, ...over.derived },
  } as never);
  return render(
    <SpritesTab
      {...panelProps(ch, { patch: over.patch ?? (() => {}) })}
      catalog={makeCatalog({ sprites: catalogSprites as never })}
    />,
  );
}

describe("<SpritesTab>", () => {
  it("compiles or registers a sprite from the catalog, and says which", () => {
    const patch = vi.fn();
    renderTab({ patch });

    fireEvent.click(screen.getAllByRole("button", { name: "コンパイル" })[0]);
    expect(patch).toHaveBeenCalledWith({
      sprites: [{ sprite_id: "courier", level: 1, registered: false }],
    });

    fireEvent.click(screen.getAllByRole("button", { name: "登録" })[1]);
    expect(patch).toHaveBeenLastCalledWith({
      sprites: [{ sprite_id: "crack", level: 1, registered: true }],
    });
  });

  it("narrows the catalog by name, in either language", () => {
    renderTab();
    // by placeholder as well as by name: it is the only prompt the box has
    expect(screen.getByPlaceholderText("スプライトを検索")).toBeDefined();
    const search = screen.getByRole("searchbox", { name: "スプライトを検索" });

    fireEvent.change(search, { target: { value: "crack" } });
    expect(screen.queryByText("Courier Sprite")).toBeNull();
    expect(screen.getByText("Crack Sprite")).toBeDefined();

    fireEvent.change(search, { target: { value: "  " } });
    expect(screen.getByText("Courier Sprite")).toBeDefined();
  });

  // A compiled sprite is gone at the next reboot and a registered one is not,
  // which is the whole difference between the two on this tab.
  it("marks a compiled sprite as lasting only until a reboot", () => {
    renderTab({ sprites: [owned()] });
    expect(
      screen.getByText(/コンパイル \/ L3 \/ タスク 2 \/ 再起動またはリブートまで/),
    ).toBeDefined();
  });

  it("does not say that about a registered one", () => {
    renderTab({ sprites: [owned({ registered: true })] });
    expect(screen.getByText(/登録 \/ L3 \/ タスク 2 \/ SR5/)).toBeDefined();
    expect(screen.queryByText(/再起動またはリブートまで/)).toBeNull();
  });

  it("writes the level and the tasks back to the saved row", () => {
    const patch = vi.fn();
    renderTab({ sprites: [owned()], patch });

    fireEvent.change(screen.getByRole("spinbutton", { name: /レベル/ }), {
      target: { value: "5" },
    });
    expect(patch).toHaveBeenLastCalledWith({ sprites: [expect.objectContaining({ level: 5 })] });

    // spending a task invalidates the test that was rolled for it
    fireEvent.change(screen.getByRole("spinbutton", { name: "タスク" }), {
      target: { value: "1" },
    });
    expect(patch).toHaveBeenLastCalledWith({
      sprites: [expect.objectContaining({ services: 1, hits: null, opposed_hits: null })],
    });
  });

  it("keeps an emptied hit field empty rather than calling it zero", () => {
    const patch = vi.fn();
    renderTab({ sprites: [owned({ hits: 4, opposed_hits: 2 })], patch });

    fireEvent.change(screen.getByRole("spinbutton", { name: "コンパイルヒット" }), {
      target: { value: "" },
    });
    expect(patch).toHaveBeenLastCalledWith({ sprites: [expect.objectContaining({ hits: null })] });

    fireEvent.change(screen.getByRole("spinbutton", { name: "スプライトヒット" }), {
      target: { value: "3" },
    });
    expect(patch).toHaveBeenLastCalledWith({
      sprites: [expect.objectContaining({ opposed_hits: 3 })],
    });
  });

  it("registers a compiled sprite in place, and deletes one outright", () => {
    const patch = vi.fn();
    renderTab({ sprites: [owned(), owned({ id: "s2", sprite_id: "crack" })], patch });

    fireEvent.change(screen.getAllByRole("combobox", { name: "種類" })[0], {
      target: { value: "registered" },
    });
    expect(patch).toHaveBeenLastCalledWith({
      sprites: [
        expect.objectContaining({ id: "s1", registered: true }),
        expect.objectContaining({ id: "s2", registered: false }),
      ],
    });

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);
    expect(patch).toHaveBeenLastCalledWith({
      sprites: [expect.objectContaining({ id: "s2" })],
    });
  });

  it("prints the matrix attributes, the fade test and the powers it has", () => {
    renderTab({
      sprites: [
        owned({
          matrix: { attack: 3, sleaze: 5, dataprocessing: 4, firewall: 3, initiative: "8+4d6" },
          test: { attrs: ["RES", "WIL"], pool: 9 },
          powers: [{ name: "Hash" }],
        }),
      ],
    });
    expect(screen.getByText(/ATK 3 ・ SLZ 5 ・ DP 4 ・ FW 3 ・ INI 8\+4d6/)).toBeDefined();
    expect(screen.getByText("Hash")).toBeDefined();
    expect(screen.getByText(/RES/)).toBeDefined();
  });

  // The preamble is the only place the living persona and the fade pool are
  // shown at all, and both are optional.
  it("shows the living persona and the fade pool only once the engine sends them", () => {
    renderTab();
    expect(screen.queryByText(/リビングペルソナ/)).toBeNull();

    renderTab({
      derived: {
        fade_resist: { attrs: "RES + WIL", pool: 9 },
        living_persona: {
          device_rating: 5,
          attack: 2,
          sleaze: 3,
          dataprocessing: 5,
          firewall: 4,
        },
      },
    });
    expect(screen.getByText(/リビングペルソナ DR5 ATK2 SLZ3 DP5 FW4/)).toBeDefined();
  });
});
