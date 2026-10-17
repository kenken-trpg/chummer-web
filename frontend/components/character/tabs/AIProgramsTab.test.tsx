import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { AIProgramsTab } from "@/components/character/tabs/AIProgramsTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { InstalledAIProgram } from "@/lib/types";

const program = (name: string, category: string, extra: Record<string, unknown> = {}) => ({
  id: name.toLowerCase(),
  name,
  category,
  advanced: category === "Advanced Programs",
  required: [] as string[],
  needs_extra: false,
  source: "SR5",
  page: "245",
  ...extra,
});

const catalog = makeCatalog({
  ai_programs: [
    program("Browse", "Common Programs"),
    program("Exploit", "Hacking Programs"),
    program("Authority", "Advanced Programs", { required: ["Exploit"], source: "DT" }),
  ],
});

const owned = (name: string, extra: Partial<InstalledAIProgram> = {}): InstalledAIProgram => ({
  id: `own-${name}`,
  program_id: name.toLowerCase(),
  name,
  category: "Hacking Programs",
  advanced: false,
  required: [],
  needs_extra: false,
  extra: "",
  free: false,
  granted_by: "",
  karma: 5,
  ...extra,
});

function renderTab(
  programs: InstalledAIProgram[] = [],
  patch: (b: Record<string, unknown>) => void = () => {},
) {
  const ch = makeCharacter({
    metatype: "A.I.",
    ai_programs: programs
      .filter((p) => !p.free)
      .map((p) => ({ id: p.id, program_id: p.program_id })),
    derived: { enabled_tabs: ["DEP", "advanced programs"], ai_programs: programs },
  });
  return render(<AIProgramsTab {...panelProps(ch, { catalog, patch })} />);
}

const pickerRow = (name: string) =>
  [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
    el.querySelector("b")?.textContent?.includes(name),
  ) as HTMLElement;

describe("<AIProgramsTab>", () => {
  it("prices a program at 5 karma and an advanced one at 8", () => {
    renderTab();
    expect(pickerRow("Browse").textContent).toContain("5カルマ");
    expect(pickerRow("Authority").textContent).toContain("8カルマ");
  });

  it("adds a program via patch", () => {
    const patch = vi.fn();
    renderTab([], patch);
    fireEvent.click(pickerRow("Browse").querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ ai_programs: [{ program_id: "browse" }] });
  });

  it("holds an advanced program back until its base program is there", () => {
    renderTab();
    expect((pickerRow("Authority").querySelector("button") as HTMLButtonElement).disabled).toBe(
      true,
    );
    document.body.innerHTML = "";
    renderTab([owned("Exploit")]);
    expect((pickerRow("Authority").querySelector("button") as HTMLButtonElement).disabled).toBe(
      false,
    );
  });

  it("lists the Inherent Program pick as free, with nothing to delete", () => {
    renderTab([
      owned("Exploit", { id: "inherent:q", free: true, karma: 0, granted_by: "Inherent Program" }),
    ]);
    const row = document.querySelector(".cyber-item") as HTMLElement;
    expect(row.textContent).toContain("Inherent Program で無料");
    expect(row.querySelector("button")).toBeNull();
  });

  it("narrows the list to one category", () => {
    renderTab();
    fireEvent.change(screen.getByRole("combobox", { name: "カテゴリー" }), {
      target: { value: "Advanced Programs" },
    });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Authority"]);
  });
});
