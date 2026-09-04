import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { ContactsTab } from "@/components/character/tabs/ContactsTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <ContactsTab
      catalog={makeCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
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
      character: { contacts: [contact() as any], derived: { contacts: [contact()] as any } },
      patch,
    });
    expect(screen.getByText("Mr. Johnson")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenCalledWith({ contacts: [] });
  });

  it("edits Connection through a patch", () => {
    const patch = vi.fn();
    renderTab({
      character: { contacts: [contact() as any], derived: { contacts: [contact()] as any } },
      patch,
    });
    fireEvent.change(screen.getByLabelText("Connection"), { target: { value: "5" } });
    expect(patch).toHaveBeenCalledWith({
      contacts: [expect.objectContaining({ id: "c1", connection: 5 })],
    });
  });

  it("hides delete for a quality-locked row", () => {
    renderTab({
      character: {
        contacts: [contact() as any],
        derived: { contacts: [contact({ locked: true })] as any },
      },
    });
    expect(screen.queryByRole("button", { name: "削除" })).toBeNull();
    expect(screen.getByText("品質連動")).toBeDefined();
  });
});
