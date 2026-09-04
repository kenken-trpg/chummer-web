import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { MetaTab } from "@/components/character/tabs/MetaTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const priorityTable = {
  Heritage: {
    E: {
      metatypes: [
        { name: "Human", special: 0, variants: [] },
        { name: "Elf", special: 0, variants: [] },
      ],
    },
  },
  Talent: { E: { talents: [{ name: "Mundane", label: "Mundane", value: 0 }] } },
} as any;

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <MetaTab
      catalog={over.catalog ?? makeCatalog({ priority_table: priorityTable })}
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

describe("<MetaTab>", () => {
  it("lists the Heritage-priority metatypes and patches the pick", () => {
    const patch = vi.fn();
    renderTab({ patch });
    expect(screen.getByRole("button", { name: /Human/ })).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /Elf/ }));
    expect(patch).toHaveBeenCalledWith({ metatype: "Elf", metavariant: null });
  });

  it("marks the current metatype selected and offers the Talent select", () => {
    renderTab({ character: { metatype: "Human" } });
    expect(screen.getByRole("button", { name: /Human/ }).className).toContain("selected");
    expect(screen.getByRole("combobox")).toBeDefined();
  });

  it("shows the metavariant select when the chosen metatype has variants", () => {
    const patch = vi.fn();
    const catalog = makeCatalog({
      priority_table: priorityTable,
      metatypes: [{ name: "Elf", metavariants: [{ name: "Night One" }] }] as any,
    });
    renderTab({ catalog, character: { metatype: "Elf" }, patch });
    const selects = screen.getAllByRole("combobox");
    const metavariant = selects[0];
    fireEvent.change(metavariant, { target: { value: "Night One" } });
    expect(patch).toHaveBeenCalledWith({ metavariant: "Night One" });
  });

  it("in Karma build it lists catalog metatypes with a karma cost", () => {
    const patch = vi.fn();
    const catalog = makeCatalog({
      metatypes: [
        { name: "Human", karma: 0, metavariants: [] },
        { name: "Ork", karma: 0, metavariants: [] },
      ] as any,
      karma_talents: [{ name: "Mundane", label: "Mundane" }],
    } as any);
    renderTab({ catalog, character: { build_method: "Karma" }, patch });
    fireEvent.click(screen.getByRole("button", { name: /Ork/ }));
    expect(patch).toHaveBeenCalledWith({ metatype: "Ork", metavariant: null });
  });
});
