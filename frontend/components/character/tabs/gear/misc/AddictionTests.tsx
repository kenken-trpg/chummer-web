"use client";
import type { TabPanelProps } from "@/components/character/types";

/**
 * The Addiction Test (SR5 p.414), which the character makes against a drug's
 * Addiction Threshold — BOD + WIL for a physiological habit, LOG + WIL for a
 * psychological one. Chummer tracks the first dose apart from the test an
 * already-addicted character makes, so both are shown when a quality tells
 * them apart (`Drug Tolerant`, CF p.54, is +2 only the first time).
 */
export function AddictionTests({ d, ui }: Pick<TabPanelProps, "d" | "ui">) {
  const totals = d.totals || {};
  const wil = totals.WIL || 0;
  const mods = d.test_mods || {};
  const pools: [string, number, number][] = [
    [
      ui("gear.addictionPhysiological"),
      (totals.BOD || 0) + wil + (mods.addiction_physiological_first || 0),
      (totals.BOD || 0) + wil + (mods.addiction_physiological_addicted || 0),
    ],
    [
      ui("gear.addictionPsychological"),
      (totals.LOG || 0) + wil + (mods.addiction_psychological_first || 0),
      (totals.LOG || 0) + wil + (mods.addiction_psychological_addicted || 0),
    ],
  ];
  return (
    <div className="muted" style={{ marginBottom: 8 }}>
      {ui("gear.addictionTest")}:{" "}
      {pools
        .map(([label, first, addicted]) =>
          first === addicted
            ? `${label} ${first}`
            : `${label} ${first} (${ui("gear.addictionAddicted")} ${addicted})`,
        )
        .join(" ／ ")}
    </div>
  );
}
