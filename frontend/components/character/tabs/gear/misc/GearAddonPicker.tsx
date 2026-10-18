"use client";
import type { TabPanelProps } from "@/components/character/types";
import { trAs } from "@/lib/ui-strings";
import { isBookEnabled, useAllowedBooks } from "@/lib/character/books";
import { alreadySlotted, miscFits } from "@/lib/character/gear";
import type { InstalledGear } from "@/lib/types";

/** What can be slotted into one piece of gear (or, for a drug, the grade it
 *  is cut to), the target such an add-on asks for, and the button that
 *  installs it. Nothing when nothing fits. */
export function GearAddonPicker({
  item,
  catalog,
  character: ch,
  tr,
  ui,
  patch,
  childrenItems,
  slotPick,
  setSlotPick,
  extraPick,
  setExtraPick,
  mode,
}: Pick<TabPanelProps, "catalog" | "character" | "tr" | "ui" | "patch"> & {
  item: InstalledGear;
  childrenItems: InstalledGear[];
  mode: "misc" | "drugs";
  slotPick: Record<string, string>;
  setSlotPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
  extraPick: Record<string, string>;
  setExtraPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
}) {
  const allowedBooks = useAllowedBooks();
  const addons = (catalog.gear || []).filter(
    (mod) => Boolean(mod.requireparent) && miscFits(item, mod),
  );
  const addonSpec = (catalog.gear || []).find((mod) => mod.id === (slotPick[item.id] || ""));
  if (!addons.length) return null;
  return (
    <div className="cyber-controls">
      <select
        aria-label={`${tr(item.name)}: ${mode === "drugs" ? ui("gear.gradeOrAddon") : ui("gear.addGear")}`}
        value={slotPick[item.id] || ""}
        onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
      >
        <option value="">{mode === "drugs" ? ui("gear.gradeOrAddon") : ui("gear.addGear")}</option>
        {addons
          .filter((mod) => !alreadySlotted(mod, childrenItems))
          // Drug grades are not a book: they are how the one drug in
          // this row is cut, so they are always on offer.
          .filter(
            (mod) =>
              mod.category === "Drug Grades" ||
              isBookEnabled(allowedBooks, mod.source, mod.also_in),
          )
          .map((mod) => (
            <option key={mod.id} value={mod.id}>
              {tr(mod.name)} ({mod.cost}¥)
            </option>
          ))}
      </select>
      {addonSpec?.extra_kind === "skill" || addonSpec?.extra_kind === "text" ? (
        addonSpec.extra_kind === "skill" ? (
          <select
            aria-label={`${tr(item.name)}: ${ui("common.target")}`}
            value={extraPick[item.id] || ""}
            onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
          >
            <option value="">{ui("common.target")}</option>
            {(addonSpec.extra_options || []).map((name) => (
              <option key={name} value={name}>
                {trAs(tr, addonSpec.extra_skill_kind, name)}
              </option>
            ))}
          </select>
        ) : (
          <>
            <input
              list={`gear-addon-extra-${item.id}`}
              placeholder={ui("common.target")}
              value={extraPick[item.id] || ""}
              onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
            />
            <datalist id={`gear-addon-extra-${item.id}`}>
              {(addonSpec.extra_options || []).slice(0, 80).map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </>
        )
      ) : null}
      <button
        className="btn"
        disabled={!slotPick[item.id]}
        onClick={() => {
          const wareId = slotPick[item.id];
          const spec = addons.find((mod) => mod.id === wareId);
          if (!spec) return;
          patch({
            gear: [
              ...(ch.gear || []),
              {
                gear_id: spec.id,
                rating: Math.max(1, spec.minrating || 1),
                parent_id: item.id,
                extra: extraPick[item.id] || undefined,
              },
            ],
          });
          setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
          setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
        }}
      >
        {ui("common.install")}
      </button>
    </div>
  );
}
