import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { GearReview } from "@/components/character/GearReview";
import type { PendingGear } from "@/lib/api";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr } from "@/tests/fixtures";

function row(over: Partial<PendingGear> = {}): PendingGear {
  return {
    name: "アレス・サンダートラック・ガウスライフル",
    rating: 0,
    qty: 1,
    note: "",
    suggestions: [
      {
        bucket: "weapons",
        key: "weapons",
        id: "w1",
        name: "Ares Thunderstruck Gauss Rifle",
        entry: { id: "new", weapon_id: "w1", qty: 1 },
      },
    ],
    ...over,
  };
}

function makeEd(over: Partial<CharacterEditor> = {}): CharacterEditor {
  return {
    tr: identityTr,
    ch: { id: "c1", weapons: [{ id: "old", weapon_id: "w0" }] },
    pendingGear: null,
    patch: vi.fn().mockResolvedValue(undefined),
    resolvePendingGear: vi.fn(),
    dismissPendingGear: vi.fn(),
    ...over,
  } as unknown as CharacterEditor;
}

describe("<GearReview>", () => {
  it("renders nothing when the import left nothing to confirm", () => {
    const { container } = render(<GearReview ed={makeEd()} />);
    expect(container.innerHTML).toBe("");
    expect(render(<GearReview ed={makeEd({ pendingGear: [] })} />).container.innerHTML).toBe("");
  });

  it("shows what the sheet said about a row it could not match", () => {
    render(
      <GearReview
        ed={makeEd({ pendingGear: [row({ qty: 3, rating: 4, note: "AP-4。100発分" })] })}
      />,
    );
    screen.getByText("アレス・サンダートラック・ガウスライフル");
    expect(screen.getByLabelText(/装備シート/).textContent).toContain("3 個・レーティング 4");
    expect(screen.getByLabelText(/装備シート/).textContent).toContain("AP-4。100発分");
  });

  it("appends the suggestion's own row to the list it names", async () => {
    const ed = makeEd({ pendingGear: [row()] });
    render(<GearReview ed={ed} />);

    fireEvent.click(screen.getByRole("button", { name: /Ares Thunderstruck Gauss Rifle/ }));
    await waitFor(() =>
      expect(ed.patch).toHaveBeenCalledWith({
        weapons: [
          { id: "old", weapon_id: "w0" },
          { id: "new", weapon_id: "w1", qty: 1 },
        ],
      }),
    );
    // and the row is done with, however it was settled
    await waitFor(() =>
      expect(ed.resolvePendingGear).toHaveBeenCalledWith(
        "アレス・サンダートラック・ガウスライフル",
      ),
    );
  });

  it("starts the list when the character has none of that kind yet", async () => {
    const ed = makeEd({ ch: { id: "c1" } as never, pendingGear: [row()] });
    render(<GearReview ed={ed} />);
    fireEvent.click(screen.getByRole("button", { name: /Ares Thunderstruck/ }));
    await waitFor(() =>
      expect(ed.patch).toHaveBeenCalledWith({ weapons: [{ id: "new", weapon_id: "w1", qty: 1 }] }),
    );
  });

  it("says which tab a suggestion would land on, since a name does not", () => {
    const shield = row({
      name: "バリスティックシールド",
      suggestions: [
        { bucket: "weapons", key: "weapons", id: "w2", name: "Ballistic Shield", entry: {} },
        { bucket: "armor", key: "armor", id: "a2", name: "Ballistic Shield", entry: {} },
      ],
    });
    render(<GearReview ed={makeEd({ pendingGear: [shield] })} />);
    // the same name twice, told apart by the tab each one would land on
    screen.getByRole("button", { name: "Ballistic Shield武器" });
    screen.getByRole("button", { name: "Ballistic Shield防具" });
  });

  it("admits when nothing in the book looks like the row", () => {
    render(<GearReview ed={makeEd({ pendingGear: [row({ suggestions: [] })] })} />);
    screen.getByText("近いものが見つかりませんでした");
  });

  it("lets a row be skipped without adding anything", () => {
    const ed = makeEd({ pendingGear: [row()] });
    render(<GearReview ed={ed} />);
    fireEvent.click(screen.getByRole("button", { name: "飛ばす" }));
    expect(ed.patch).not.toHaveBeenCalled();
    expect(ed.resolvePendingGear).toHaveBeenCalledWith("アレス・サンダートラック・ガウスライフル");
  });

  it("lets the whole panel be closed", () => {
    const ed = makeEd({ pendingGear: [row()] });
    render(<GearReview ed={ed} />);
    fireEvent.click(screen.getByRole("button", { name: "残りをまとめて閉じる" }));
    expect(ed.dismissPendingGear).toHaveBeenCalled();
  });
});
