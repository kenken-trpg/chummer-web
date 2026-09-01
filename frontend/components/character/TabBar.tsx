import type { Tab } from "@/lib/character/constants";

export function TabBar({
  tab,
  setTab,
  enabledTabs,
}: {
  tab: Tab;
  setTab: (t: Tab) => void;
  enabledTabs: string[];
}) {
  return (
    <div className="tabs">
      {(
        [
          ["priority", "優先度"],
          ["meta", "メタ"],
          ["attrs", "能力値"],
          ["skills", "技能"],
          ["qualities", "資質"],
          ["cyber", "サイバー"],
          ["bio", "バイオ"],
          ["gear", "ギア"],
          ["contacts", "コンタクト"],
          ["martial", "武道"],
          ...(enabledTabs.includes("initiation")
            ? [["initiation", "イニシエーション"] as const]
            : []),
          ...(enabledTabs.includes("submersion")
            ? [["submersion", "サブマージョン"] as const]
            : []),
          ...(enabledTabs.includes("adept") ? [["adept", "アデプト"] as const] : []),
          ...(enabledTabs.includes("spells") ? [["spells", "術式"] as const] : []),
          ...(enabledTabs.includes("spirits") ? [["spirits", "精霊"] as const] : []),
          ...(enabledTabs.includes("foci") ? [["foci", "フォーカス"] as const] : []),
          ...(enabledTabs.includes("complexforms") ? [["complexforms", "複合体"] as const] : []),
          ...(enabledTabs.includes("sprites") ? [["sprites", "スプライト"] as const] : []),
          ["sheet", "シート"],
        ] as const
      ).map(([k, label]) => (
        <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>
          {label}
        </button>
      ))}
    </div>
  );
}
