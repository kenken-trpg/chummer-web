"use client";
import { useMemo } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { RangeInput } from "@/components/character/RangeInput";
import { HelpTip } from "@/components/help/HelpTip";
import { SpecPicker } from "@/components/character/SpecPicker";
import { ACTIVE_SKILL_CATS, skillCatLabel } from "@/lib/character/constants";
import { defaultBit, skillsoftBit, specBit } from "@/lib/character/bits";
import { skillDefault } from "@/lib/character/skill-default";
import { skillDice } from "@/lib/character/format";
import { KarmaLevels, SpecKarma, skillLimits, specEditor } from "./shared";

export function ActiveSkills(props: TabPanelProps) {
  const { catalog, character: ch, d, tr, ui, patch, setCharacter } = props;
  const { skillMax, splitKarma, karmaSplit } = skillLimits(props);
  const spec = specEditor(props);

  const expertiseBySkill = useMemo(() => {
    const map = new Map<string, { spec: string; bonus: number; source?: string }>();
    for (const row of d.skill_expertises || []) {
      if (row.skill && row.spec) {
        map.set(row.skill, { spec: row.spec, bonus: row.bonus || 3, source: row.source });
      }
    }
    return map;
  }, [d.skill_expertises]);

  /**
   * The active skills in the order the rulebook prints them: by category
   * (SR5 p.130 — Combat, Physical, Social, Magical, Resonance, Technical,
   * Vehicle), alphabetical inside each. The vendored file's own order is
   * neither — it opens with Technical Active and runs Magical before Combat —
   * so a reader coming from the book or the official sheet had to hunt.
   *
   * `active_categories` is the catalog's copy of that order; the constant is
   * the fallback, and any category the catalog grows later lands after them
   * rather than being dropped.
   */
  const activeByCategory = useMemo(() => {
    const order = catalog.skills.active_categories?.length
      ? catalog.skills.active_categories
      : [...ACTIVE_SKILL_CATS];
    const rank = new Map(order.map((cat, i) => [cat, i]));
    const buckets = new Map<string, typeof catalog.skills.skills>();
    for (const s of catalog.skills.skills) {
      if (s.source !== "SR5" || s.name.includes("Exotic")) continue;
      const bucket = buckets.get(s.category);
      if (bucket) bucket.push(s);
      else buckets.set(s.category, [s]);
    }
    return [...buckets.entries()]
      .sort(([a], [b]) => (rank.get(a) ?? order.length) - (rank.get(b) ?? order.length))
      .map(([category, list]) => ({
        category,
        // English name, so the order matches the book rather than the reading
        // of whichever Japanese gloss we happen to ship.
        skills: [...list].sort((a, b) => a.name.localeCompare(b.name)),
      }));
  }, [catalog]);

  /** The one-line "what am I about to drag" for an active-skill row: the
   *  linked attribute and category, plus whatever the engine says is already
   *  modifying it. A `<swapskillattribute>` replaces the printed attribute
   *  outright; the spec-limited variant only earns a trailing note. */
  function skillHint(name: string, attribute: string, category: string): string {
    return skillHintLines(name, attribute, category).join(" / ");
  }

  /** The row's own facts, one per line: the linked attribute and category, the
   *  creation cap, and whatever the engine says already modifies it. A
   *  `<swapskillattribute>` replaces the printed attribute outright; the
   *  spec-limited variant only earns a trailing note. */
  function skillHintLines(name: string, attribute: string, category: string): string[] {
    const swaps = (d.skill_attribute_swaps || []).filter((row) => row.skill === name);
    const swap = swaps.find((row) => !row.spec);
    const specSwap = swaps.find((row) => row.spec);
    return [
      ui("skills.rowHint", {
        attr: swap ? swap.attribute : attribute,
        category: skillCatLabel(category, ui),
        max: skillMax + (d.skill_max_bonus?.[name] || 0),
      }),
      ...(swap ? [ui("skills.attrSwap", { attr: swap.attribute, source: tr(swap.source) })] : []),
      ...(specSwap
        ? [ui("skills.specAttrSwap", { attr: specSwap.attribute, spec: tr(specSwap.spec) })]
        : []),
      ...(d.skill_bonus_notes?.[name] || []),
    ];
  }

  /** The row's facts plus the terms behind them — the same glossary on every
   *  skill, so "what does a specialization buy" is answered where it is used. */
  function skillHelpLines(name: string, attribute: string, category: string) {
    return [
      ...skillHintLines(name, attribute, category).map((label) => ({ label })),
      { label: ui("help.skill.pool") },
      { label: ui("help.skill.spec") },
      { label: ui("help.skill.default") },
      { label: ui("help.skill.cap") },
    ];
  }

  return (
    <>
      <h3>{ui("skills.active")}</h3>
      {activeByCategory.map(({ category, skills }) => (
        <div key={category}>
          <h4 className="skill-cat">{skillCatLabel(category, ui)}</h4>
          {skills.map((s) => {
            const expertise = expertiseBySkill.get(s.name);
            const specValue = expertise?.spec || ch.skill_specializations?.[s.name] || "";
            const hasSkill =
              (ch.skills[s.name] || 0) > 0 ||
              (d.skill_totals[s.name] || 0) > 0 ||
              (d.skillsoft?.[s.name] || 0) > 0;
            return (
              <div
                className={splitKarma ? "skill-row has-spec has-karma" : "skill-row has-spec"}
                key={s.id}
              >
                <span>
                  <HelpTip
                    label={ui("help.open", { label: tr(s.name) })}
                    lines={skillHelpLines(s.name, s.attribute, s.category)}
                  >
                    {tr(s.name)}
                  </HelpTip>
                </span>
                <RangeInput
                  min={0}
                  max={skillMax + (d.skill_max_bonus?.[s.name] || 0)}
                  value={ch.skills[s.name] || d.skill_totals[s.name] || 0}
                  label={tr(s.name)}
                  title={skillHint(s.name, s.attribute, s.category)}
                  onDraft={(value) =>
                    setCharacter({ ...ch, skills: { ...ch.skills, [s.name]: value } })
                  }
                  onCommit={(value) => patch({ skills: { ...ch.skills, [s.name]: value } })}
                />
                <KarmaLevels
                  name={s.name}
                  rating={ch.skills[s.name] || 0}
                  levels={karmaSplit?.levels}
                  field="skill_karma"
                  props={props}
                />
                <span className="spec-cell">
                  <SpecPicker
                    options={[...(s.specs || []), ...(d.skill_spec_options?.[s.name] || [])]}
                    value={specValue}
                    disabled={!hasSkill || Boolean(expertise)}
                    tr={tr}
                    onDraft={(next) => spec.draft(s.name, next)}
                    onCommit={(next) => spec.commit(s.name, next)}
                  />
                  {expertise ? null : <SpecKarma name={s.name} spec={specValue} props={props} />}
                </span>
                <b>
                  {hasSkill ? (
                    <>
                      {skillDice(
                        Math.max(d.skill_totals[s.name] || 0, d.skillsoft?.[s.name] || 0),
                        d.skill_bonus?.[s.name],
                      )}
                      {skillsoftBit(d.skillsoft?.[s.name], ui)}
                      {specBit(specValue, tr(specValue), ui, expertise?.bonus || 2)}
                    </>
                  ) : (
                    // Nothing bought: what the skill still rolls at, defaulting.
                    defaultBit(skillDefault(s, d), ui)
                  )}
                </b>
              </div>
            );
          })}
        </div>
      ))}
    </>
  );
}
