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
    <div className="tabs">
      {TABS.filter(([k, always]) => always || enabledTabs.includes(k)).map(([k]) => (
        <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>
          {ui(`tab.${k}` as MsgKey)}
        </button>
      ))}
    </div>
  );
}
