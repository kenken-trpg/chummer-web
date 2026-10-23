"use client";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree } from "@/lib/character/gear";
import { editRow } from "@/lib/character/rows";
import type { InstalledGear } from "@/lib/types";

/** One thing slotted into, or carried inside, a piece of gear — and whatever
 *  it holds in turn. A container's contents nest as deep as the player (or
 *  Chummer) put them: Narcoject in Injection Darts in a Spare Clip. Rendering
 *  only the first level left the rest owned but invisible. */
export function GearChild({
  child,
  all,
  ch,
  tr,
  ui,
  patch,
  depth = 0,
}: Pick<TabPanelProps, "tr" | "ui" | "patch"> & {
  child: InstalledGear;
  all: InstalledGear[];
  ch: TabPanelProps["character"];
  depth?: number;
}) {
  const kids = all.filter((row) => row.parent_id === child.id);
  return (
    <div className="muted" style={{ marginTop: 6, marginLeft: depth * 12 }}>
      {tr(child.label || child.name)}
      {child.rating_max > 0 ? ` R${child.rating}` : ""}
      {child.qty > 1 ? ` ×${child.qty}` : ""}
      {child.included ? ` / ${ui("common.included")}` : ` / ${child.nuyen.toLocaleString()}¥`}
      {child.capacity_cost ? ` / ${ui("common.capacity")} ${child.capacity_cost}` : ""}
      {child.included ? null : (
        <>
          {" "}
          <button
            className="btn danger"
            aria-label={ui("common.removeLabel", { name: tr(child.label || child.name) })}
            onClick={() => patch({ gear: dropTree(ch.gear || [], child.id) })}
          >
            {ui("common.remove")}
          </button>
          {/* carried inside, not plugged in: it can be taken out and kept.
              Something that needs a host has nowhere to go. */}
          {child.requireparent ? null : (
            <>
              {" "}
              <button
                className="btn"
                aria-label={ui("gear.takeOutLabel", { name: tr(child.label || child.name) })}
                onClick={() => patch({ gear: editRow(ch.gear, child.id, { parent_id: null }) })}
              >
                {ui("gear.takeOut")}
              </button>
            </>
          )}
        </>
      )}
      {child.rating_max > 0 && !child.included ? (
        <label>
          {ui("common.rating")}
          <input
            type="number"
            min={1}
            max={child.rating_max}
            value={child.rating}
            onChange={(e) =>
              patch({ gear: editRow(ch.gear, child.id, { rating: Number(e.target.value) }) })
            }
          />
        </label>
      ) : null}
      {kids.map((kid) => (
        <GearChild
          key={kid.id}
          child={kid}
          all={all}
          ch={ch}
          tr={tr}
          ui={ui}
          patch={patch}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}
