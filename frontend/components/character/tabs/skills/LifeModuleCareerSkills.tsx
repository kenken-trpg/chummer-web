"use client";

import { useRef, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import type { LifeModuleSkillAdvancement } from "@/lib/types";

export function LifeModuleCareerSkills({
  character: ch,
  catalog,
  d,
  ui,
  tr,
  trGroup,
  patch,
}: TabPanelProps) {
  const [kind, setKind] = useState<LifeModuleSkillAdvancement["kind"]>("active");
  const [target, setTarget] = useState("");
  const [specific, setSpecific] = useState("");
  const [levels, setLevels] = useState(1);
  const [category, setCategory] = useState<LifeModuleSkillAdvancement["category"]>("Professional");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const sending = useRef(false);
  const rows = ch.life_module_skill_advancements || [];
  const options =
    kind === "group"
      ? catalog.skills.groups.map((g) => ({ id: g, name: trGroup(g) }))
      : catalog.skills.skills
          .filter(
            (s) =>
              Boolean(s.exotic) === (kind === "exotic") &&
              !d.life_module_skills?.unavailable_skill_ids?.includes(s.id),
          )
          .map((s) => ({ id: s.id, name: tr(s.name) }));

  async function save(next: LifeModuleSkillAdvancement[]) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setFailed(false);
    try {
      await patch({ life_module_skill_advancements: next });
    } catch {
      setFailed(true);
    } finally {
      sending.current = false;
      setBusy(false);
    }
  }

  return (
    <fieldset disabled={busy}>
      <legend>{ui("life.growth.title")}</legend>
      <p className="muted">{ui("life.growth.note")}</p>
      <div className="life-choices">
        <label>
          {ui("life.growth.kind")}
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value as typeof kind);
              setTarget("");
              setSpecific("");
            }}
          >
            <option value="active">{ui("life.kind.skills")}</option>
            <option value="exotic">{ui("skills.exotic")}</option>
            <option value="group">{ui("life.kind.skill_groups")}</option>
            <option value="knowledge">{ui("life.kind.knowledge_skills")}</option>
          </select>
        </label>
        <label>
          {ui("life.growth.target")}
          {kind === "knowledge" ? (
            <input value={target} maxLength={200} onChange={(e) => setTarget(e.target.value)} />
          ) : (
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">{ui("life.pending")}</option>
              {options.map((s) => (
                <option value={s.id} key={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          )}
        </label>
        {kind === "exotic" && (
          <label>
            {ui("life.transfer.specific")}
            <input maxLength={200} value={specific} onChange={(e) => setSpecific(e.target.value)} />
          </label>
        )}
        {kind === "knowledge" && (
          <label>
            {ui("life.kind.knowledge_categories")}
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as typeof category)}
            >
              {["Academic", "Professional", "Street", "Interest", "Language"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        )}
        <label>
          {ui("life.growth.levels")}
          <input
            type="number"
            min={1}
            max={kind === "knowledge" ? d.knowledge_rating_max : d.skill_rating_max}
            step={1}
            value={levels}
            onChange={(e) => setLevels(Number(e.target.value))}
          />
        </label>
        <button
          disabled={
            !target.trim() ||
            !Number.isInteger(levels) ||
            levels < 1 ||
            (kind === "exotic" && !specific.trim())
          }
          onClick={() =>
            save([
              ...rows,
              {
                id: crypto.randomUUID(),
                kind,
                target_id: target.trim(),
                specific: specific.trim(),
                levels,
                category,
              },
            ])
          }
        >
          {ui("life.growth.add")}
        </button>
      </div>
      {(d.life_module_skills?.growth_lines || []).map((line) => (
        <p key={line.id}>
          {line.kind === "group"
            ? trGroup(line.target_id)
            : tr(
                catalog.skills.skills.find((s) => s.id === line.target_id)?.name || line.target_id,
              )}
          :{` ${line.from_rating} → ${line.to_rating} (${line.karma} Karma)`}
        </p>
      ))}
      {!!rows.length && (
        <button onClick={() => save(rows.slice(0, -1))}>{ui("life.growth.undo")}</button>
      )}
      {failed && (
        <p role="alert" className="error">
          {ui("life.transfer.failed")}
        </p>
      )}
    </fieldset>
  );
}
