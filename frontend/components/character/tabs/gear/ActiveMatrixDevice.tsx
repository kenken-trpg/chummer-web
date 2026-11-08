"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";

const LIVING_PERSONA = "living_persona";

/**
 * The persona the character runs — Chummer's active commlink. The Matrix
 * initiative and the sheet's Matrix row come from it. With no pick the engine
 * runs the one with the highest Data Processing; a player who carries another
 * (a spare Meta Link beside a better commlink at home) picks it here.
 *
 * Shown only when there is something to choose between, and never to an A.I.,
 * which runs from its home node.
 */
export function ActiveMatrixDevice({ character: ch, d, tr, ui, patch }: TabPanelProps) {
  if (d.condition_monitor?.core) return null;
  const options: { value: string; label: string }[] = [];
  if (d.living_persona)
    options.push({
      value: LIVING_PERSONA,
      label: ui("gear.activeDevice.option", {
        name: ui("side.livingPersona"),
        dp: d.living_persona.dataprocessing,
      }),
    });
  for (const row of [...(d.commlinks || []), ...(d.cyberdecks || []), ...(d.rccs || [])])
    options.push({
      value: row.id,
      label: ui("gear.activeDevice.option", { name: tr(row.name), dp: row.dataprocessing }),
    });
  if (options.length < 2) return null;
  const picked = ch.active_matrix_device || "";
  // a pick of something since sold or removed is the automatic one again
  const value = options.some((o) => o.value === picked) ? picked : "";
  return (
    <div className="option-row">
      <HelpTip
        label={ui("help.open", { label: ui("gear.activeDevice") })}
        lines={[{ label: ui("help.gear.activeDevice1") }, { label: ui("help.gear.activeDevice2") }]}
      >
        <label>
          {ui("gear.activeDevice")}{" "}
          <select
            value={value}
            onChange={(e) => void patch({ active_matrix_device: e.target.value })}
          >
            <option value="">{ui("gear.activeDevice.auto")}</option>
            {options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </HelpTip>
    </div>
  );
}
