"use client";

import type { TabPanelProps } from "@/components/character/types";
import { editRow } from "@/lib/character/rows";

/** Purchased software with no device selected, as Chummer saves top-level apps. */
export function LooseAppRows({
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "character" | "d" | "tr" | "ui" | "patch">) {
  const loose = (d.apps || []).filter((app) => !app.parent_id);
  if (!loose.length) return null;
  const hosts = [...(d.commlinks || []), ...(d.cyberdecks || []), ...(d.rccs || [])];

  return (
    <div className="cyber-item">
      <div>
        <b>{ui("gear.looseApps")}</b>
        {loose.map((app) => (
          <div className="muted" key={app.id} style={{ marginTop: 6 }}>
            {tr(app.label || app.name)} / {app.nuyen.toLocaleString()}¥{" "}
            {hosts.length ? (
              <label>
                {ui("gear.loadInto")}
                <select
                  value=""
                  onChange={(e) =>
                    e.target.value &&
                    patch({ apps: editRow(ch.apps, app.id, { parent_id: e.target.value }) })
                  }
                >
                  <option value="">{ui("common.selectShort")}</option>
                  {hosts.map((host) => (
                    <option key={host.id} value={host.id}>
                      {tr(host.name)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}{" "}
            <button
              className="btn danger"
              onClick={() => patch({ apps: (ch.apps || []).filter((row) => row.id !== app.id) })}
            >
              {ui("common.remove")}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
