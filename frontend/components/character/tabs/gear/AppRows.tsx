"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { PriceField } from "@/components/character/tabs/gear/PriceField";
import type { TabPanelProps } from "@/components/character/types";

/**
 * The apps on one device and the select to add more. A commlink runs them,
 * and so do a cyberdeck and an RCC — Chummer lets any of the three hold
 * `Software` (BLUE's RCC carries Swarm).
 */
export function AppRows({
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
  return (
    <>
      {(d.apps || [])
        .filter((app) => app.parent_id === hostId)
        .map((app) => (
          <div className="muted" key={app.id} style={{ marginTop: 6 }}>
            {tr(app.label || app.name)}
            {app.included
              ? ` / ${ui("common.included")}`
              : app.nuyen
                ? ` / ${app.nuyen.toLocaleString()}¥`
                : ""}{" "}
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  apps: (ch.apps || []).filter((row) => row.id !== app.id),
                })
              }
            >
              {ui("common.remove")}
            </button>
            <PriceField
              range={app.cost_range}
              value={
                (ch.apps || []).find((row) => row.id === app.id)?.cost ?? app.cost_range?.[0] ?? 0
              }
              label={tr(app.label || app.name)}
              ui={ui}
              onChange={(cost) =>
                patch({
                  apps: (ch.apps || []).map((row) => (row.id === app.id ? { ...row, cost } : row)),
                })
              }
            />
            {app.rating_max > 0 ? (
              <label title={ui("common.ratingHint")}>
                {ui("common.rating")}
                <input
                  type="number"
                  min={1}
                  max={app.rating_max}
                  value={app.rating}
                  onChange={(e) =>
                    patch({
                      apps: (ch.apps || []).map((row) =>
                        row.id === app.id ? { ...row, rating: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
            ) : null}
            {app.extra_kind === "skill" ? (
              <label>
                {ui("common.skill")}
                <select
                  value={app.extra || ""}
                  onChange={(e) =>
                    patch({
                      apps: (ch.apps || []).map((row) =>
                        row.id === app.id ? { ...row, extra: e.target.value } : row,
                      ),
                    })
                  }
                >
                  <option value="">{ui("common.selectShort")}</option>
                  {(app.extra_options || []).map((name) => (
                    <option key={name} value={name}>
                      {tr(name)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {app.extra_kind === "text" ? (
              <label>
                {ui("common.target")}
                <input
                  value={app.extra || ""}
                  onChange={(e) =>
                    patch({
                      apps: (ch.apps || []).map((row) =>
                        row.id === app.id ? { ...row, extra: e.target.value } : row,
                      ),
                    })
                  }
                />
              </label>
            ) : null}
          </div>
        ))}
      <AddonSelect
        rowName={tr(hostName)}
        prompt={ui("gear.addApp")}
        tr={tr}
        options={(catalog.apps || []).filter(
          (app) =>
            app.source === "SR5" &&
            (app.needs_extra ||
              !(d.apps || []).some((row) => row.parent_id === hostId && row.gear_id === app.id)),
        )}
        extraFor={(app) =>
          app.extra_kind === "skill"
            ? { label: ui("common.skill"), values: app.extra_options || [] }
            : null
        }
        onAdd={(app, extra) =>
          patch({
            apps: [
              ...(ch.apps || []),
              {
                gear_id: app.id,
                rating: Math.max(1, app.minrating || 1),
                parent_id: hostId,
                extra,
              },
            ],
          })
        }
      />
    </>
  );
}
