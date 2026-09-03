"use client";

import type { TabPanelProps } from "@/components/character/types";
import type { Tab } from "@/lib/character/constants";
import { buildChecklist, checklistSummary, type CheckSeverity } from "@/lib/character/checklist";
import { type MsgKey, useUiText } from "@/lib/i18n";

const DOT: Record<CheckSeverity, string> = { error: "✗", warn: "▲", info: "•" };
const GROUP_KEY: Record<CheckSeverity, MsgKey> = {
  error: "check.group.error",
  warn: "check.group.warn",
  info: "check.group.info",
};
const ORDER: CheckSeverity[] = ["error", "warn", "info"];

export function ChecklistPanel({
  panel,
  setTab,
}: {
  panel: TabPanelProps;
  setTab: (t: Tab) => void;
}) {
  const { ui } = useUiText();
  const items = buildChecklist(panel.character);
  const { errors, warns, infos, ok } = checklistSummary(items);

  return (
    <div className="checklist">
      <div className={`checklist-head ${ok ? "ok" : "bad"}`}>
        <b>{ui("check.title")}</b>
        <span>{ui("check.summary", { errors, warns, infos })}</span>
      </div>

      {items.length === 0 ? (
        <p className="ok">{ui("check.pass")}</p>
      ) : (
        ORDER.filter((sev) => items.some((i) => i.severity === sev)).map((sev) => (
          <section key={sev} className="card">
            <h3>{ui(GROUP_KEY[sev])}</h3>
            <ul className="checklist-items">
              {items
                .filter((i) => i.severity === sev)
                .map((i) => (
                  <li key={i.id} className={`ci ci-${i.severity}`}>
                    <span className="ci-dot">{DOT[i.severity]}</span>
                    <span className="ci-msg">
                      {i.message}
                      {i.ref ? <span className="muted"> — {i.ref}</span> : null}
                    </span>
                    {i.tab ? (
                      <button className="btn ci-jump" onClick={() => setTab(i.tab as Tab)}>
                        {ui("check.jump")}
                      </button>
                    ) : null}
                  </li>
                ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}
