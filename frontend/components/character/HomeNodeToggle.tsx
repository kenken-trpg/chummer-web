"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import type { Character } from "@/lib/types";

/**
 * "Home node": the device or vehicle an A.I. lives in (Chummer's `HomeNode`). One at a
 * time, so ticking another moves the mark. Shown to an A.I. only — the
 * engine drops the mark from anyone else.
 */
export function HomeNodeToggle({
  id,
  ch,
  d,
  ui,
  patch,
}: {
  id: string;
  ch: Character;
  d: Character["derived"];
  ui: TabPanelProps["ui"];
  patch: TabPanelProps["patch"];
}) {
  if (!d.condition_monitor?.core) return null;
  return (
    <HelpTip
      label={ui("help.open", { label: ui("gear.homeNode") })}
      lines={[
        { label: ui("help.gear.homeNode1") },
        { label: ui("help.gear.homeNode2") },
        { label: ui("help.gear.homeNode3") },
      ]}
    >
      <label>
        <input
          type="checkbox"
          checked={ch.home_node === id}
          onChange={(e) => patch({ home_node: e.target.checked ? id : "" })}
        />
        {ui("gear.homeNode")}
      </label>
    </HelpTip>
  );
}
