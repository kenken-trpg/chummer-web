"use client";
import { HelpTip } from "@/components/help/HelpTip";
import { AddonSelect } from "@/components/character/AddonSelect";
import type { TabPanelProps } from "@/components/character/types";
import { useBookFilter } from "@/lib/character/books";

/** The autosofts on one host — an RCC that shares them, or a drone or
 *  vehicle that runs them itself — with their picks, and the control that
 *  loads another. */
export function AutosoftRows({
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
  const byBook = useBookFilter();
  return (
    <>
      {(d.programs || [])
        .filter((prog) => prog.parent_id === hostId)
        .map((prog) => (
          <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
            <HelpTip
              label={ui("help.open", { label: tr(prog.label || prog.name) })}
              lines={[{ label: ui("help.program.slot") }, { label: ui("help.program.rating") }]}
            >
              {ui("help.program.statsLabel")}
            </HelpTip>{" "}
            {tr(prog.label || prog.name)}
            {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
            {` / ${prog.nuyen.toLocaleString()}¥`}{" "}
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  programs: (ch.programs || []).filter((row) => row.id !== prog.id),
                })
              }
            >
              {ui("common.remove")}
            </button>
            {prog.rating_max > 0 ? (
              <label title={ui("common.ratingHint")}>
                {ui("common.rating")}
                <input
                  type="number"
                  min={1}
                  max={prog.rating_max}
                  value={prog.rating}
                  onChange={(e) =>
                    patch({
                      programs: (ch.programs || []).map((row) =>
                        row.id === prog.id ? { ...row, rating: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
            ) : null}
            {prog.extra_kind === "skill" ? (
              <label>
                {ui("common.skill")}
                <select
                  value={prog.extra || ""}
                  onChange={(e) =>
                    patch({
                      programs: (ch.programs || []).map((row) =>
                        row.id === prog.id ? { ...row, extra: e.target.value } : row,
                      ),
                    })
                  }
                >
                  <option value="">{ui("common.selectShort")}</option>
                  {(prog.extra_options || []).map((name) => (
                    <option key={name} value={name}>
                      {tr(name)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {prog.extra_kind === "group" ? (
              <label>
                {ui("common.group")}
                <select
                  value={prog.extra || ""}
                  onChange={(e) =>
                    patch({
                      programs: (ch.programs || []).map((row) =>
                        row.id === prog.id ? { ...row, extra: e.target.value } : row,
                      ),
                    })
                  }
                >
                  <option value="">{ui("common.selectShort")}</option>
                  {(prog.extra_options || []).map((name) => (
                    <option key={name} value={name}>
                      {tr(name)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {prog.extra_kind === "text" ? (
              <label>
                {ui("common.target")}
                <input
                  list={`prog-extra-${prog.id}`}
                  value={prog.extra || ""}
                  onChange={(e) =>
                    patch({
                      programs: (ch.programs || []).map((row) =>
                        row.id === prog.id ? { ...row, extra: e.target.value } : row,
                      ),
                    })
                  }
                />
                <datalist id={`prog-extra-${prog.id}`}>
                  {(prog.extra_options || []).slice(0, 80).map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>
              </label>
            ) : null}
          </div>
        ))}
      <AddonSelect
        rowName={hostName}
        prompt={ui("gear.addAutosoft")}
        tr={tr}
        options={byBook(catalog.programs || []).filter(
          (prog) =>
            prog.program_host === "rccs" &&
            (prog.needs_extra ||
              !(d.programs || []).some(
                (row) => row.parent_id === hostId && row.gear_id === prog.id,
              )),
        )}
        extraFor={(prog) => {
          if (prog.extra_kind === "skill") {
            return { label: ui("common.skill"), values: prog.extra_options || [] };
          }
          if (prog.extra_kind === "group") {
            return { label: ui("common.group"), values: prog.extra_options || [] };
          }
          // a vehicle autosoft names a model, which is not a closed set
          if (prog.extra_kind === "text") {
            return {
              label: ui("common.target"),
              values: prog.extra_options || [],
              freeText: true,
            };
          }
          return null;
        }}
        onAdd={(prog, extra) =>
          patch({
            programs: [
              ...(ch.programs || []),
              {
                gear_id: prog.id,
                rating: Math.max(1, prog.minrating || 1),
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
