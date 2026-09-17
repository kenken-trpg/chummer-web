"use client";
import type { TabPanelProps } from "@/components/character/types";

/** Programs the character owns but has loaded nowhere (Chummer keeps them in
 *  the inventory), with a control to load each into a host that runs it. */
export function LooseProgramRows({
  kind,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "character" | "d" | "tr" | "ui" | "patch"> & {
  kind: "cyberdecks" | "rccs";
}) {
  const loose = (d.programs || []).filter(
    (prog) => !prog.parent_id && (prog.program_host || "cyberdecks") === kind,
  );
  if (!loose.length) return null;
  // an autosoft runs on an RCC, or on the drone or vehicle itself
  const hosts =
    kind === "cyberdecks"
      ? d.cyberdecks || []
      : [...(d.rccs || []), ...(d.drones || []), ...(d.vehicles || [])];
  const move = (id: string, parentId: string | null) =>
    patch({
      programs: (ch.programs || []).map((row) =>
        row.id === id ? { ...row, parent_id: parentId } : row,
      ),
    });
  return (
    <div className="cyber-item">
      <div>
        <b>{ui("gear.loosePrograms")}</b>
        {loose.map((prog) => (
          <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
            {tr(prog.label || prog.name)}
            {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
            {` / ${prog.nuyen.toLocaleString()}¥`}{" "}
            {hosts.length ? (
              <label>
                {ui("gear.loadInto")}
                <select value="" onChange={(e) => e.target.value && move(prog.id, e.target.value)}>
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
              onClick={() =>
                patch({ programs: (ch.programs || []).filter((row) => row.id !== prog.id) })
              }
            >
              {ui("common.remove")}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
