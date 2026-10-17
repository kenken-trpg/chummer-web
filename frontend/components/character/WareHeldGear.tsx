"use client";

import { AddonSelect } from "@/components/character/AddonSelect";
import { CarriedGearRow } from "@/components/character/tabs/gear/ArmorRows";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import type { InstalledWare } from "@/lib/types";

/** The housings' `<allowgear>` categories whose devices keep their own list
 *  (SR5 p.451-452): set up on the gear tab, only placed here. */
const IMPLANT_BUCKETS = { Commlinks: "commlinks", Cyberdecks: "cyberdecks" } as const;
type ImplantBucket = (typeof IMPLANT_BUCKETS)[keyof typeof IMPLANT_BUCKETS];

/**
 * What a piece of ware holds — a Chemical Gland's chemical, an Auto
 * Injector's drug — and the select to put one in. Only the categories its
 * `<allowgear>` names are offered; Chummer prices the gland by what is in it.
 */
export function WareHeldGear({
  item,
  catalog,
  character: ch,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "tr" | "ui" | "patch"> & { item: InstalledWare }) {
  const allowed = item.allow_gear || [];
  if (!allowed.length) return null;
  const options = (catalog.gear || []).filter(
    (row) => allowed.includes(row.category) && row.category !== "Custom",
  );
  const buckets = allowed.flatMap((category) =>
    category in IMPLANT_BUCKETS ? [IMPLANT_BUCKETS[category as keyof typeof IMPLANT_BUCKETS]] : [],
  );
  const implanted = buckets.flatMap((bucket) =>
    (ch.derived?.[bucket] || [])
      .filter((row) => row.parent_id === item.id)
      .map((row) => ({ bucket, row })),
  );
  const setParent = (bucket: ImplantBucket, id: string, parent_id: string | null) =>
    patch({
      [bucket]: (ch[bucket] || []).map((row) => (row.id === id ? { ...row, parent_id } : row)),
    });
  return (
    <>
      <div className="muted" style={{ marginTop: 6 }}>
        <HelpTip
          label={ui("help.open", { label: ui("help.heldGear.statsLabel") })}
          lines={[{ label: ui("help.heldGear.what") }, { label: ui("help.gear.qty") }]}
        >
          {ui("help.heldGear.statsLabel")}
        </HelpTip>
      </div>
      {item.modular_equipped === false && (item.gear || []).length > 0 ? (
        <p className="muted">{ui("ware.heldGearInactive")}</p>
      ) : null}
      {(item.gear || []).map((gear) => (
        <CarriedGearRow key={gear.id} gear={gear} character={ch} tr={tr} ui={ui} patch={patch} />
      ))}
      {implanted.map(({ bucket, row }) => (
        <div className="cyber-item" key={row.id}>
          <div>
            <b>{tr(row.name)}</b>
            <div className="muted">{ui("ware.implantedHint")}</div>
          </div>
          <button className="btn" onClick={() => setParent(bucket, row.id, null)}>
            {ui("ware.takeOut")}
          </button>
        </div>
      ))}
      {item.included || item.granted_by || implanted.length
        ? null
        : buckets.map((bucket) => (
            <AddonSelect
              key={bucket}
              rowName={tr(item.name)}
              prompt={ui("ware.addHeldGear")}
              addLabel={ui("gear.putIn")}
              tr={tr}
              options={catalog[bucket] || []}
              onAdd={(row) =>
                patch({
                  [bucket]: [
                    ...(ch[bucket] || []),
                    { gear_id: row.id, parent_id: item.id, rating: 1, qty: 1 },
                  ],
                })
              }
            />
          ))}
      {item.included || item.granted_by ? null : (
        <AddonSelect
          rowName={tr(item.name)}
          prompt={ui("ware.addHeldGear")}
          addLabel={ui("gear.putIn")}
          tr={tr}
          options={options}
          onAdd={(row) =>
            patch({
              gear: [
                ...(ch.gear || []),
                {
                  gear_id: row.id,
                  parent_id: item.id,
                  rating: Math.max(1, row.minrating || 1),
                  qty: 1,
                },
              ],
            })
          }
        />
      )}
    </>
  );
}
