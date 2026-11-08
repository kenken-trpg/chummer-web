import { useEffect, useRef, useState } from "react";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import type { TabPanelProps } from "./types";
import type { Tab } from "@/lib/character/constants";
import { creationBudgets } from "@/lib/character/creation-review";
import { buildChecklist, checklistSummary } from "@/lib/character/checklist";
import { ChecklistPanel } from "./ChecklistPanel";
import { useUiText } from "@/lib/i18n";
import { HelpTip } from "@/components/help/HelpTip";

export function CreationReview({
  ed,
  panel,
  setTab,
}: {
  ed: CharacterEditor;
  panel: TabPanelProps;
  setTab: (tab: Tab) => void;
}) {
  const ch = ed.careerReview;
  if (!ch) return null;
  return (
    <Review
      key={ch.id}
      ed={ed}
      panel={{ ...panel, character: ch, d: ch.derived }}
      setTab={setTab}
    />
  );
}

function Review({
  ed,
  panel,
  setTab,
}: {
  ed: CharacterEditor;
  panel: TabPanelProps;
  setTab: (tab: Tab) => void;
}) {
  const { ui, locale } = useUiText();
  const [confirming, setConfirming] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const { errors } = checklistSummary(buildChecklist(panel.character));
  const pending = ed.pendingGear?.length ?? 0;
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    heading.current?.scrollIntoView({ block: "start", behavior: "smooth" });
  }, []);
  function jump(tab: Tab) {
    ed.cancelCareerReview();
    setTab(tab);
  }
  return (
    <section className="card" aria-labelledby="creation-review-title" aria-busy={confirming}>
      <h2 ref={heading} id="creation-review-title" tabIndex={-1} style={{ scrollMarginTop: 100 }}>
        {ui("app.creationReview.title")}
      </h2>
      <p>
        <HelpTip
          label={ui("help.open", { label: ui("app.creationReview.title") })}
          lines={[
            { label: ui("help.review.negative") },
            { label: ui("help.review.baseline") },
            { label: ui("help.review.back") },
          ]}
        >
          {ui("app.creationReview.description", {
            name: panel.character.name || ui("toolbar.unnamed"),
          })}
        </HelpTip>
      </p>
      <div className="table-scroll">
        <table>
          <caption>{ui("app.creationReview.budgets")}</caption>
          <thead>
            <tr>
              <th scope="col">{ui("app.creationReview.item")}</th>
              <th scope="col">{ui("app.creationReview.remaining")}</th>
              <th scope="col">{ui("app.roster.action")}</th>
            </tr>
          </thead>
          <tbody>
            {creationBudgets(panel.character).map((row) => (
              <tr key={row.label}>
                <th scope="row">{ui(row.label)}</th>
                <td className={row.remaining < 0 ? "errors" : undefined}>
                  {row.remaining.toLocaleString(locale)}
                </td>
                <td>
                  <button
                    className="btn"
                    disabled={confirming}
                    onClick={() => jump(row.tab)}
                    aria-label={ui("app.creationReview.edit", { name: ui(row.label) })}
                  >
                    {ui("check.jump")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pending ? (
        <p className="warn">
          {ui("app.creationReview.pending", { count: pending })}{" "}
          <button className="btn" disabled={confirming} onClick={() => jump("gear")}>
            {ui("check.jump")}
          </button>
        </p>
      ) : null}
      <ChecklistPanel panel={panel} setTab={jump} disabled={confirming} />
      {errors ? <p className="warn">{ui("app.creationReview.errors")}</p> : null}
      {ed.error ? (
        <p className="errors" role="alert">
          {ed.error}
        </p>
      ) : null}
      <button
        className="btn primary"
        disabled={confirming}
        onClick={async () => {
          setConfirming(true);
          try {
            await ed.confirmCareerReview();
          } finally {
            setConfirming(false);
          }
        }}
      >
        {ui(confirming ? "app.creationReview.confirming" : "app.creationReview.confirm")}
      </button>{" "}
      <button className="btn" disabled={confirming} onClick={ed.cancelCareerReview}>
        {ui("app.creationReview.cancel")}
      </button>
    </section>
  );
}
