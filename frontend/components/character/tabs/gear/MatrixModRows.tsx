"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree } from "@/lib/character/gear";

/**
 * The Electronic Modifications (DT p.66) soldered into one matrix device.
 *
 * A commlink, a cyberdeck and an RCC all take them, and each is free: what
 * they cost is the point they move — Increase Attack buys Attack and two
 * boxes of the device's matrix condition monitor, and on a deck a
 * "Modify Matrix Attribute" trades one array slot against another. The three
 * device tabs are otherwise unalike enough that only this block is shared.
 */
export function MatrixModRows({
  hostId,
  hostName,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  hostId: string;
  hostName: string;
}) {
  const installed = (d.gear || []).filter((row) => row.parent_id === hostId);
  return (
    <>
      {installed.map((mod) => (
        <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
          {tr(mod.label || mod.name)}
          {mod.included ? ` / ${ui("common.included")}` : ` / ${mod.nuyen.toLocaleString()}¥`}{" "}
          <button
            className="btn danger"
            aria-label={ui("common.removeLabel", { name: tr(mod.label || mod.name) })}
            onClick={() => patch({ gear: dropTree(ch.gear || [], mod.id) })}
          >
            {ui("common.remove")}
          </button>
        </div>
      ))}
      <AddonSelect
        rowName={hostName}
        prompt={ui("gear.addModification")}
        tr={tr}
        options={(catalog.gear || []).filter(
          (mod) =>
            mod.category === "Electronic Modification" &&
            !installed.some((row) => row.gear_id === mod.id),
        )}
        onAdd={(mod) =>
          patch({
            gear: [
              ...(ch.gear || []),
              { gear_id: mod.id, rating: Math.max(1, mod.minrating || 1), parent_id: hostId },
            ],
          })
        }
      />
    </>
  );
}
