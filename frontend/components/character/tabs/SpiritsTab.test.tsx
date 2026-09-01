import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SpiritsTab } from "@/components/character/tabs/SpiritsTab";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const traditions = [{ id: "hermetic", name: "Hermetic", drain_attrs: ["WIL", "LOG"] }];
const spirits = [{ id: "fire", name: "Fire Spirit", source: "SR5", attributes: {} }];

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <SpiritsTab
      catalog={
        over.catalog ?? makeCatalog({ traditions: traditions as any, spirits: spirits as any })
      }
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<SpiritsTab>", () => {
  it("renders the tradition select", () => {
    renderTab();
    expect(screen.getByRole("combobox")).toBeDefined();
  });

  it("sets the tradition through patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "hermetic" } });
    expect(patch).toHaveBeenCalledWith({ tradition_id: "hermetic" });
  });

  it("summons and binds a tradition spirit via patch", () => {
    const patch = vi.fn();
    renderTab({
      character: { derived: { tradition: { spirits: { Combat: "Fire Spirit" } } as any } },
      patch,
    });
    fireEvent.click(screen.getByRole("button", { name: "召喚" }));
    expect(patch).toHaveBeenCalledWith({
      spirits: [{ spirit_id: "fire", force: 1, services: 1, bound: false }],
    });
    fireEvent.click(screen.getByRole("button", { name: "結合" }));
    expect(patch).toHaveBeenCalledWith({
      spirits: [{ spirit_id: "fire", force: 1, services: 1, bound: true }],
    });
  });
});
