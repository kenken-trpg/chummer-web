"use client";

import { useId } from "react";
import type { SkillPickSlot } from "@/lib/types";
import { useUiText } from "@/lib/i18n";

export function SkillPickSelects(props: {
  slots: SkillPickSlot[];
  tr: (name: string) => string;
  onPick: (key: string, skill: string) => void;
}) {
  const { ui } = useUiText();
  const id = useId();
  if (!props.slots.length) return null;
  return (
    <div className="skill-picks">
      {props.slots.map((slot) => {
        const empty = slot.options.length === 0;
        const minimum = slot.minimum_rating || 0;
        const hintId = `${id}-${slot.key}-hint`;
        return (
          <div key={slot.key}>
            <label>
              {ui("pick.skillOf", { source: props.tr(slot.source) })}
              {slot.bonus ? ` ${slot.bonus > 0 ? "+" : ""}${slot.bonus}` : ""}
              {slot.max ? ui("pick.max", { max: slot.max }) : ""}
              {slot.rating ? ui("pick.rating", { rating: slot.rating }) : ""}
              {slot.accuracy ? ui("pick.accuracy", { accuracy: slot.accuracy }) : ""}
              {/* Reflex Recorder Optimization widens the pick to its whole group. */}
              {slot.default_free ? ui("pick.noDefaultPenalty") : ""}
              <select
                value={slot.picked}
                disabled={empty}
                aria-describedby={minimum || empty ? hintId : undefined}
                onChange={(e) => props.onPick(slot.key, e.target.value)}
              >
                <option value="">{ui(empty ? "pick.noEligibleSkills" : "common.choose")}</option>
                {slot.options.map((name) => (
                  <option key={name} value={name}>
                    {props.tr(name)}
                  </option>
                ))}
              </select>
            </label>
            {minimum || empty ? (
              <p className="muted" id={hintId}>
                {minimum > 0 ? ui("pick.minimumRating", { rating: minimum }) : null}
                {empty
                  ? ` ${ui(minimum > 0 ? "pick.raiseSkillRating" : "pick.checkSkills", { rating: minimum })}`
                  : null}
              </p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
