import type { Tab } from "@/lib/character/constants";
import { type MsgKey, useUiText } from "@/lib/i18n";

// [tab, always-shown]. The awakened / emerged tabs appear only when the engine
// reports them in `enabled_tabs`.
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
    <nav className="tabs" aria-label={ui("nav.sections")}>
      {TABS.filter(([k, always]) => always || enabledTabs.includes(k)).map(([k]) => (
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
      ))}
    </nav>
  );
}
