import type { Tab } from "@/lib/character/constants";
import { type MsgKey, useUiText } from "@/lib/i18n";
import type { Derived } from "@/lib/types";

// [tab, always-shown]. The awakened / emerged tabs appear only when the engine
// reports them in `enabled_tabs`.

/** A tab the engine enables under another name: an A.I.'s metatype says
 *  `<enabletab>advanced programs`, an Infected's or a drake's quality
 *  `<enabletab>critter`. */
export const TAB_GATES: Partial<Record<Tab, string>> = {
  aiprograms: "advanced programs",
  critterpowers: "critter",
};

/** The engine's `enabled_tabs`, less a Critter Powers tab with nothing in it.
 *  A shapeshifter's or a metasapient's metatype opens that tab too, but names
 *  no category to buy from; Chummer then lists every power, most at no karma
 *  because the data gives them no price. Here the tab stays shut until a
 *  quality names a category, or a loaded save already holds a bought power.
 *  `enabled_tabs` itself is left alone: the .chum5 export writes it. */
export function shownTabs(
  d: Pick<Derived, "enabled_tabs" | "critter_power_categories" | "critter_powers">,
): string[] {
  const critter = d.critter_power_categories?.length || d.critter_powers?.length;
  return critter ? d.enabled_tabs : d.enabled_tabs.filter((t) => t !== "critter");
}
const TABS: [Tab, boolean][] = [
  ["priority", true],
  ["meta", true],
  ["attrs", true],
  ["skills", true],
  ["qualities", true],
  ["cyber", true],
  ["bio", true],
  ["gear", true],
  ["contacts", true],
  ["martial", true],
  ["initiation", false],
  ["submersion", false],
  ["adept", false],
  ["spells", false],
  ["spirits", false],
  ["foci", false],
  ["complexforms", false],
  ["sprites", false],
  ["aiprograms", false],
  ["critterpowers", false],
  ["check", true],
  ["sheet", true],
];

export function TabBar({
  tab,
  setTab,
  enabledTabs,
}: {
  tab: Tab;
  setTab: (t: Tab) => void;
  enabledTabs: string[];
}) {
  const { ui } = useUiText();
  return (
    // Plain buttons in a nav rather than role="tablist"/role="tab": that
    // pattern also owes the user arrow-key navigation and aria-controls, and a
    // half-implemented tablist announces a contract the page does not keep.
    <nav className="tabs no-print" aria-label={ui("nav.sections")}>
      {TABS.filter(([k, always]) => always || enabledTabs.includes(TAB_GATES[k] ?? k)).map(
        ([k]) => (
          <button
            key={k}
            className={`tab ${tab === k ? "active" : ""}`}
            aria-current={tab === k ? "true" : undefined}
            // one line on what the section is for — the labels are short enough
            // to be guessable but not short enough to be obvious ("メタ", "資質")
            title={ui(`tab.${k}.hint` as MsgKey)}
            onClick={() => setTab(k)}
          >
            {ui(`tab.${k}` as MsgKey)}
          </button>
        ),
      )}
    </nav>
  );
}
