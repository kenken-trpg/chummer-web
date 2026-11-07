import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { ContactsTab } from "@/components/character/tabs/ContactsTab";
import { makeCharacter, panelProps } from "@/tests/fixtures";

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(<ContactsTab {...panelProps(ch, { patch: over.patch ?? (() => {}) })} />);
}

const contact = (over: Record<string, unknown> = {}) => ({
  id: "c1",
  name: "Mr. Johnson",
  role: "Fixer",
  connection: 3,
  loyalty: 2,
  cost: 5,
  connection_max: 6,
  loyalty_max: 6,
  ...over,
});

describe("<ContactsTab>", () => {
  it("shows the chargen point line and no rows for an empty character", () => {
    renderTab();
    expect(screen.getByText(/無料枠 CHA×3 = 0\/0/)).toBeDefined();
    expect(screen.getByText(/作成時は合計7まで/)).toBeDefined();
    expect(document.querySelectorAll(".cyber-item")).toHaveLength(0);
  });

  it("shows the settings file's multiplier in the point line", () => {
    renderTab({
      character: { derived: { contact_points: { used: 2, free: 18, paid: 0, free_mult: 6 } } },
    });
    expect(screen.getByText(/無料枠 CHA×6 = 2\/18/)).toBeDefined();
  });

  it("explains the point line, with the settings file's multiplier", () => {
    renderTab({
      character: { derived: { contact_points: { used: 2, free: 18, paid: 0, free_mult: 6 } } },
    });
    expect(screen.getByRole("button", { name: "コンタクトの点数 の説明" })).toBeDefined();
    expect(screen.getByText(/無料の点数は魅力×6。/)).toBeDefined();
    expect(screen.getByText(/資質の決めた分を差し引いて数える/)).toBeDefined();
    expect(screen.getByText(/超えた分はカルマで払う/)).toBeDefined();
  });

  it("adds a contact through the toolbar, appending to the patch payload", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByPlaceholderText("名前"), { target: { value: "Fence" } });
    fireEvent.change(screen.getByPlaceholderText("役割（任意）"), { target: { value: "Fixer" } });
    fireEvent.click(screen.getByRole("button", { name: "追加" }));
    expect(patch).toHaveBeenCalledWith({
      contacts: [{ name: "Fence", role: "Fixer", connection: 1, loyalty: 1 }],
    });
  });

  it("renders an existing contact and deletes it via patch", () => {
    const patch = vi.fn();
    renderTab({
      character: { contacts: [contact() as never], derived: { contacts: [contact()] as never } },
      patch,
    });
    expect(screen.getByText("Mr. Johnson")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenCalledWith({ contacts: [] });
  });

  it("edits the connection rating through a patch", () => {
    const patch = vi.fn();
    renderTab({
      character: { contacts: [contact() as never], derived: { contacts: [contact()] as never } },
      patch,
    });
    fireEvent.change(screen.getByLabelText("コネ値"), { target: { value: "5" } });
    expect(patch).toHaveBeenCalledWith({
      contacts: [expect.objectContaining({ id: "c1", connection: 5 })],
    });
  });

  it("hides delete for a quality-locked row", () => {
    renderTab({
      character: {
        contacts: [contact() as never],
        derived: { contacts: [contact({ locked: true })] as never },
      },
    });
    expect(screen.queryByRole("button", { name: "削除" })).toBeNull();
    expect(screen.getByText("資質連動")).toBeDefined();
  });

  it("keeps a contact's own description and saves it on leaving the field", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        contacts: [{ id: "c1", name: "Mr. Johnson", location: "Seattle", notes: "Owes us one." }],
        derived: { contacts: [contact()] },
      } as never,
    });

    const box = screen.getByText("詳しい情報（所在地・メタタイプ・備考など）").closest("details")!;
    // something is written there, so it opens on its own
    expect(box.open).toBe(true);
    expect((screen.getByRole("textbox", { name: "所在地" }) as HTMLInputElement).value).toBe(
      "Seattle",
    );
    const notes = screen.getByRole("textbox", { name: "備考" });
    expect((notes as HTMLTextAreaElement).value).toBe("Owes us one.");
    fireEvent.focusOut(notes, { target: { value: "Owes us two." } });
    expect(patch.mock.calls.at(-1)![0].contacts[0].notes).toBe("Owes us two.");
    fireEvent.focusOut(screen.getByRole("textbox", { name: "支払い方法" }), {
      target: { value: "Cash" },
    });
    expect(patch.mock.calls.at(-1)![0].contacts[0].preferred_payment).toBe("Cash");
  });

  it("leaves the description closed while nothing is written there", () => {
    renderTab({
      character: {
        contacts: [{ id: "c1", name: "Mr. Johnson" }],
        derived: { contacts: [contact()] },
      } as never,
    });
    const box = screen.getByText("詳しい情報（所在地・メタタイプ・備考など）").closest("details")!;
    expect(box.open).toBe(false);
  });

  it("offers no description for a contact kept nowhere (a Life Module's)", () => {
    renderTab({
      character: { contacts: [], derived: { contacts: [contact()] } } as never,
    });
    expect(screen.queryByText("詳しい情報（所在地・メタタイプ・備考など）")).toBeNull();
  });
});
