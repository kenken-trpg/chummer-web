"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import type { TabPanelProps } from "@/components/character/types";
import type { GearInstall } from "@/lib/types";
import { catalogExtraOptions } from "@/lib/character/gear";

export const DECK_BUILDER = "d85c6437-7611-47d3-b4c7-4e581e5349a4";

/** Split one physical item while keeping the purchase total and all choices. */
export function installOneModule(rows: GearInstall[], id: string, parentId: string): GearInstall[] {
  return rows.flatMap((r) =>
    r.id !== id
      ? [r]
      : (r.qty ?? 1) > 1
        ? [
            { ...r, qty: (r.qty ?? 1) - 1 },
            { ...r, id: crypto.randomUUID(), qty: 1, parent_id: parentId },
          ]
        : [{ ...r, parent_id: parentId }],
  );
}

export function DeckModuleRows({
  hostId,
  hostName,
  hardwired = false,
  used,
  max,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  hostId: string;
  hostName: string;
  hardwired?: boolean;
  used: number;
  max: number;
}) {
  const installed = (d.gear || []).filter(
    (r) => r.category === "Cyberdeck Modules" && r.parent_id === hostId,
  );
  const loose = (d.gear || []).filter((r) => r.category === "Cyberdeck Modules" && !r.parent_id);
  return (
    <div className="matrix-modules">
      <b>
        {ui(hardwired ? "gear.hardwiredModulePool" : "gear.normalModulePool")} /{" "}
        {ui("gear.modulesCount", { used, max })}
      </b>
      <p className="muted">{ui("gear.moduleHelp")}</p>
      {installed.map((r) => (
        <div key={r.id} className="muted">
          {tr(r.label || r.name)} ×{r.qty} / {r.nuyen.toLocaleString()}¥
          {!r.module_valid ? ` / ${ui("gear.moduleInvalid")}` : ""}
          {!r.module_effect_supported ? ` / ${ui("gear.moduleManualEffect")}` : ""}
          <label>
            <input
              type="checkbox"
              checked={r.equipped ?? true}
              aria-label={ui("gear.moduleEnabledName", { name: tr(r.name) })}
              onChange={(e) =>
                patch({
                  gear: (ch.gear || []).map((g) =>
                    g.id === r.id ? { ...g, equipped: e.target.checked } : g,
                  ),
                })
              }
            />
            {ui("gear.moduleEnabled")}
          </label>
          {r.needs_extra ? (
            <label>
              {ui("common.target")}
              <input
                list={`module-picks-${r.id}`}
                value={r.extra || ""}
                onChange={(e) =>
                  patch({
                    gear: (ch.gear || []).map((g) =>
                      g.id === r.id ? { ...g, extra: e.target.value } : g,
                    ),
                  })
                }
              />
              <datalist id={`module-picks-${r.id}`}>
                {catalogExtraOptions(catalog.gear, r.gear_id).map((p) => (
                  <option key={p} value={p}>
                    {tr(p)}
                  </option>
                ))}
              </datalist>
            </label>
          ) : null}
          <button
            className="btn"
            aria-label={ui("gear.moduleDetachName", { name: tr(r.name) })}
            onClick={() =>
              patch({
                gear: (ch.gear || []).map((g) => (g.id === r.id ? { ...g, parent_id: null } : g)),
              })
            }
          >
            {ui("gear.moduleDetach")}
          </button>
          <button
            className="btn danger"
            aria-label={ui("common.deleteLabel", { name: tr(r.name) })}
            onClick={() => patch({ gear: (ch.gear || []).filter((g) => g.id !== r.id) })}
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      {used < max ? (
        <>
          {loose.length ? (
            <label>
              {ui("gear.moduleFromInventory")}
              <select
                value=""
                onChange={(e) => {
                  if (e.target.value)
                    patch({ gear: installOneModule(ch.gear || [], e.target.value, hostId) });
                }}
              >
                <option value="">{ui("common.selectShort")}</option>
                {loose.map((r) => (
                  <option key={r.id} value={r.id}>
                    {tr(r.label || r.name)} ×{r.qty}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <AddonSelect
            rowName={hostName}
            prompt={ui("gear.buyModule")}
            tr={tr}
            options={(catalog.gear || []).filter((r) => r.category === "Cyberdeck Modules")}
            extraFor={(r) =>
              r.needs_extra
                ? {
                    label: ui("common.target"),
                    freeText: true,
                    values: catalogExtraOptions(catalog.gear, r.id),
                  }
                : null
            }
            onAdd={(r, extra) =>
              patch({
                gear: [
                  ...(ch.gear || []),
                  { gear_id: r.id, rating: 1, qty: 1, parent_id: hostId, extra },
                ],
              })
            }
          />
        </>
      ) : (
        <p className="muted">{ui("gear.modulePoolFull")}</p>
      )}
    </div>
  );
}
