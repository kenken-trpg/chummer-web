import { render, screen, waitFor } from "@testing-library/react";
import { TabPanels } from "@/components/character/TabPanels";
import type { Tab } from "@/lib/character/constants";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

/** `PriorityTab` reads every cell of the table, so a bare catalog is not
 *  enough to render it at all. Only the shape matters here. */
const priorityTable = Object.fromEntries(
  ["Heritage", "Attributes", "Talent", "Skills", "Resources"].map((k) => [
    k,
    Object.fromEntries(
      ["A", "B", "C", "D", "E"].map((l) => [
        l,
        { name: `${l} - ${k}`, metatypes: [], talents: [] },
      ]),
    ),
  ]),
);

/**
 * The tabs are split: the chargen path is in the first bundle, the heavy and
 * the conditional panels arrive when they are opened. Nothing else in the
 * suite renders this file — each tab is tested on its own — so this is the
 * only place a broken `dynamic()` boundary would show up before CI's
 * Playwright run.
 */
function renderAt(tab: Tab) {
  const ch = makeCharacter({ derived: { enabled_tabs: ["spells"] } as never });
  return render(
    <TabPanels
      tab={tab}
      panel={panelProps(ch, {
        catalog: makeCatalog({ priority_table: priorityTable as never }),
      })}
      sheetLayout="standard"
      onPortraitFile={() => {}}
      setTab={() => {}}
    />,
  );
}

describe("<TabPanels>", () => {
  it("draws a statically imported tab on the first render", () => {
    renderAt("priority");
    // no waiting: `priority` is what the app opens on, so it is in the bundle
    expect(screen.getByRole("button", { name: "優先度" })).toBeDefined();
  });

  it("loads a lazily imported tab, saying so while it arrives", async () => {
    renderAt("gear");
    expect(screen.getByText("読み込み中…")).toBeDefined();
    await waitFor(() => expect(screen.getByRole("button", { name: "防具" })).toBeDefined());
  });

  it("loads a tab that is behind enabled_tabs", async () => {
    renderAt("spells");
    await waitFor(() => expect(screen.queryByText("読み込み中…")).toBeNull());
    // the panel resolved and rendered rather than staying on the placeholder
    expect(screen.queryByRole("button", { name: "優先度" })).toBeNull();
  });

  it("renders nothing for a tab the character has not enabled", () => {
    const { container } = renderAt("sprites");
    expect(container.textContent).toBe("");
  });
});
