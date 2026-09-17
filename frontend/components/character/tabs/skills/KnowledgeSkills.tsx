"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { RangeInput } from "@/components/character/RangeInput";
import { SpecPicker } from "@/components/character/SpecPicker";
import { KNOW_CATS, knowCatLabel } from "@/lib/character/constants";
import { skillsoftBit, specBit } from "@/lib/character/bits";
import { DEFAULT_PENALTY } from "@/lib/character/skill-default";
import { skillDice } from "@/lib/character/format";
import { KarmaLevels, knowledgeEditor, skillLimits, specEditor } from "./shared";

/** The knowledge skills the character has, with the notes that apply to all. */
export function KnowledgeSkills(props: TabPanelProps) {
  const { catalog, character: ch, d, tr, ui, setCharacter } = props;
  const { skillMax, knowledgeMax, career, splitKarma, karmaSplit } = skillLimits(props);
  const spec = specEditor(props);
  const know = knowledgeEditor(props);
  const catalogKnowledge = new Set((catalog.skills.knowledge || []).map((item) => item.name));
  const blockedKnowCats = (KNOW_CATS as readonly string[]).filter((cat) =>
    (d.blocked_default_categories || []).includes(cat),
  );

  return (
    <>
      <h3>{ui("skills.knowledge")}</h3>
      {/* Knowledge rows only exist for skills the character bought, so the
          defaulting numbers go on one line rather than on 195 rows of their
          own. Every knowledge skill hangs off INT or LOG, so that is two
          numbers — plus whatever Uneducated took away (SR5 p.80). */}
      <p className="muted">
        {ui("skills.knowDefault", {
          int: Math.max(0, (d.totals?.INT || 0) - DEFAULT_PENALTY),
          log: Math.max(0, (d.totals?.LOG || 0) - DEFAULT_PENALTY),
        })}
        {blockedKnowCats.length
          ? ui("skills.knowDefaultBlocked", {
              categories: blockedKnowCats.map((cat) => knowCatLabel(cat, ui)).join("・"),
            })
          : ""}
      </p>
      <p className="muted">
        {ui("skills.knowledgeFree")}
        {career
          ? ui("skills.knowledgeCareerRange", { max: skillMax })
          : ui("skills.knowledgeChargenRange")}
        {ui("skills.rangeSuffix")}
        {career ? ui("skills.knowledgeCareerCost") : ui("skills.knowledgeChargenCost")}
      </p>
      {Object.keys(d.skill_category_bonus || {}).length ? (
        <p className="muted">
          {Object.entries(d.skill_category_bonus || {})
            .filter(([, bonus]) => bonus)
            .map(
              ([name, bonus]) =>
                `${(KNOW_CATS as readonly string[]).includes(name) ? knowCatLabel(name, ui) : tr(name)} ${
                  bonus > 0 ? "+" : ""
                }${bonus}`,
            )
            .join(` ${ui("common.termSep")} `)}
        </p>
      ) : null}
      {(d.knowledge_skills || []).length ? (
        (d.knowledge_skills || []).map((row) => {
          const custom = !catalogKnowledge.has(row.name);
          const specValue = ch.skill_specializations?.[row.name] || row.spec || "";
          const knowSpec = (catalog.skills.knowledge || []).find((item) => item.name === row.name);
          return (
            <div className={splitKarma ? "know-row has-karma" : "know-row"} key={row.name}>
              <span>
                <HelpTip
                  label={ui("help.open", { label: tr(row.name) })}
                  lines={[
                    { label: row.attribute },
                    ...(d.skill_bonus_notes?.[row.name] || []).map((label) => ({ label })),
                    { label: ui("help.knowledge.what") },
                    { label: ui("help.skill.pool") },
                    { label: ui("help.knowledge.free") },
                    { label: ui("help.knowledge.cost") },
                    { label: ui("help.skill.spec") },
                  ]}
                >
                  {tr(row.name)}
                  {custom ? ui("skills.custom") : ""}
                </HelpTip>
              </span>
              {custom ? (
                <select
                  value={row.category}
                  onChange={(e) =>
                    know.send({
                      knowledge_categories: {
                        ...(ch.knowledge_categories || {}),
                        [row.name]: e.target.value,
                      },
                    })
                  }
                >
                  {KNOW_CATS.map((cat) => (
                    <option key={cat} value={cat}>
                      {knowCatLabel(cat, ui)}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="muted">{knowCatLabel(row.category, ui)}</span>
              )}
              {row.native ? (
                <span className="muted">{ui("skills.free")}</span>
              ) : (
                <RangeInput
                  min={1}
                  max={knowledgeMax}
                  value={ch.knowledge_skills[row.name] || row.rating}
                  label={tr(row.name)}
                  title={ui("skills.ratingHint", { max: knowledgeMax })}
                  onDraft={(value) =>
                    setCharacter({
                      ...ch,
                      knowledge_skills: { ...ch.knowledge_skills, [row.name]: value },
                    })
                  }
                  onCommit={(value) =>
                    know.send({
                      knowledge_skills: { ...ch.knowledge_skills, [row.name]: value },
                    })
                  }
                />
              )}
              <KarmaLevels
                name={row.name}
                rating={row.native ? 0 : ch.knowledge_skills[row.name] || row.rating}
                levels={karmaSplit?.knowledge_levels}
                field="knowledge_karma"
                props={props}
              />
              <SpecPicker
                options={knowSpec?.specs || []}
                value={specValue}
                tr={tr}
                onDraft={(next) => spec.draft(row.name, next)}
                onCommit={(next) => spec.commit(row.name, next)}
              />
              <b>
                {row.native
                  ? ui("skills.native")
                  : skillDice(Math.max(row.rating, row.skillsoft || 0), d.skill_bonus?.[row.name])}
                {row.native ? null : skillsoftBit(row.skillsoft, ui)}
                {specBit(specValue, tr(specValue), ui)}
              </b>
              <span className="option-row" style={{ margin: 0, gap: 6 }}>
                {row.category === "Language" ? (
                  <label className="native">
                    <input
                      type="checkbox"
                      checked={row.native}
                      onChange={(e) => know.setNative(row.name, e.target.checked)}
                    />
                    {ui("skills.native")}
                  </label>
                ) : null}
                <button className="btn danger" onClick={() => know.remove(row.name)}>
                  {ui("common.delete")}
                </button>
              </span>
            </div>
          );
        })
      ) : (
        <p className="muted">{ui("skills.emptyKnowledge")}</p>
      )}
    </>
  );
}
