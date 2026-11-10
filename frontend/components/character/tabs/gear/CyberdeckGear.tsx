"use client";
import { RowNotes } from "@/components/character/RowNotes";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { HomeNodeToggle } from "@/components/character/HomeNodeToggle";
import { DeckModuleRows, DECK_BUILDER } from "./DeckModuleRows";
import { AppRows } from "@/components/character/tabs/gear/AppRows";
import { LooseProgramRows } from "@/components/character/tabs/gear/LooseProgramRows";
import { MatrixModRows } from "@/components/character/tabs/gear/MatrixModRows";
import { CustomDeckAttributes } from "@/components/character/tabs/gear/CustomDeckAttributes";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import { useBookFilter } from "@/lib/character/books";
import { DEFAULT_ARRAY_ORDER, MATRIX_ATTRS } from "@/lib/character/constants";
import { dropTree, swapMatrixOrder } from "@/lib/character/gear";
import { sourceBit } from "@/lib/character/format";
import { editRow } from "@/lib/character/rows";
import { BoundedNumberInput } from "@/components/character/BoundedNumberInput";

export function CyberdeckGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const byBook = useBookFilter();
  return (
    <>
      {(ch.quality_ids || []).includes(DECK_BUILDER) ? (
        <label>
          {ui("gear.deckBuilderTarget")}
          <select
            value={
              ch.deck_builder_deck_id || (d.cyberdecks?.length === 1 ? d.cyberdecks[0].id : "")
            }
            onChange={(e) => patch({ deck_builder_deck_id: e.target.value || null })}
          >
            <option value="">{ui("common.selectShort")}</option>
            {(d.cyberdecks || []).map((r) => (
              <option key={r.id} value={r.id}>
                {tr(r.name)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <LooseProgramRows kind="cyberdecks" character={ch} d={d} tr={tr} ui={ui} patch={patch} />
      <>
        {(d.cyberdecks || []).length ? <p className="muted">{ui("deck.arrayNote")}</p> : null}
        {(d.cyberdecks || []).map((item) => (
          <div data-sheet-search={`cyberdecks/${item.id}`} className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              {item.implanted_in ? (
                <div className="muted">
                  {ui("gear.implantedIn", { name: tr(item.implanted_in) })}
                </div>
              ) : null}
              <div className="muted">
                {item.name} / DR {item.device_rating} / ATK {item.attack} / SLZ {item.sleaze} / DP{" "}
                {item.dataprocessing} / FW {item.firewall}
                {ui("gear.deckPrograms", {
                  installed: item.program_installed ?? 0,
                  used: item.program_used ?? 0,
                  max: item.program_max ?? item.programs ?? 0,
                })}{" "}
                / {item.nuyen.toLocaleString()}¥{item.free ? ui("gear.freePurchase") : ""} /{" "}
                {sourceBit(item, ui)}
              </div>
              <div className="cyber-controls">
                <DiscountToggle
                  list="cyberdecks"
                  id={item.id}
                  ch={ch}
                  d={d}
                  ui={ui}
                  patch={patch}
                />
                <HomeNodeToggle id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
              </div>
              {item.rating_max > 0 ? (
                <div className="cyber-controls">
                  <label>
                    {ui("common.rating")}
                    <BoundedNumberInput
                      min={1}
                      max={item.rating_max}
                      value={item.rating}
                      onCommit={(n) =>
                        patch({
                          cyberdecks: editRow(ch.cyberdecks, item.id, {
                            rating: n,
                          }),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              <CustomDeckAttributes
                deckId={item.id}
                deckName={item.name}
                deckRating={item.rating}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
              {item.can_reorder && (item.array || []).length === 4 ? (
                <div className="matrix-array">
                  {MATRIX_ATTRS.map(([key, label]) => (
                    <label key={key}>
                      <HelpTip
                        label={ui("help.open", { label })}
                        lines={[
                          { label: ui(`help.matrix.${key}`) },
                          { label: ui("help.matrix.array") },
                        ]}
                      >
                        {label}
                      </HelpTip>
                      <select
                        aria-label={label}
                        value={String((item.array_order || DEFAULT_ARRAY_ORDER).indexOf(key))}
                        onChange={(e) =>
                          patch({
                            cyberdecks: editRow(ch.cyberdecks, item.id, {
                              array_order: swapMatrixOrder(
                                item.array_order,
                                key,
                                Number(e.target.value),
                              ),
                            }),
                          })
                        }
                      >
                        {(item.array || []).map((n, i) => (
                          <option key={`${key}-${i}`} value={i}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              ) : null}
              {d.overclocker ? (
                <div className="cyber-controls">
                  <label>
                    {ui("gear.overclocker")}
                    <select
                      aria-label={ui("gear.overclocker")}
                      value={item.overclocked ?? ""}
                      onChange={(e) =>
                        patch({
                          cyberdecks: editRow(ch.cyberdecks, item.id, {
                            overclocked: (e.target.value || null) as typeof item.overclocked,
                          }),
                        })
                      }
                    >
                      <option value="">{ui("gear.overclockerAuto")}</option>
                      {MATRIX_ATTRS.map(([key, label]) => (
                        <option key={key} value={key}>
                          {label} +1
                        </option>
                      ))}
                      <option value="none">{ui("gear.overclockerNone")}</option>
                    </select>
                  </label>
                </div>
              ) : null}
              {(d.programs || [])
                .filter((prog) => prog.parent_id === item.id)
                .map((prog) => (
                  <div
                    data-sheet-search={`programs/${prog.id}`}
                    className="muted"
                    key={prog.id}
                    style={{ marginTop: 6 }}
                  >
                    <HelpTip
                      label={ui("help.open", { label: tr(prog.name) })}
                      lines={[
                        { label: ui("help.program.deckSlot") },
                        { label: ui("help.program.rating") },
                      ]}
                    >
                      {ui("help.program.statsLabel")}
                    </HelpTip>{" "}
                    {tr(prog.name)}
                    {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
                    {prog.attribute_bonus
                      ? ui("gear.programAttrBonus", {
                          attr:
                            MATRIX_ATTRS.find(([key]) => key === prog.attribute_bonus)?.[1] ??
                            prog.attribute_bonus,
                        })
                      : ""}
                    {` / ${prog.nuyen.toLocaleString()}¥`}{" "}
                    <label>
                      <input
                        type="checkbox"
                        aria-label={ui("gear.programRunningName", { name: tr(prog.name) })}
                        // a Program Carrier keeps it running (DT p.65)
                        disabled={!!prog.carried_by}
                        checked={prog.running ?? true}
                        onChange={(e) => {
                          // read now: the updater runs later, once React has set the
                          // controlled box back to what the character says
                          const running = e.target.checked;
                          // composed from the saved character: ticking two programs in a
                          // row would otherwise send a second body that differs from the
                          // first in two places, which the editor drops
                          patch((cur) => ({
                            programs: editRow(cur.programs, prog.id, { running }),
                          }));
                        }}
                      />
                      {ui(prog.carried_by ? "gear.programCarried" : "gear.programRunning")}
                    </label>{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch((cur) => ({
                          programs: (cur.programs || []).filter((row) => row.id !== prog.id),
                        }))
                      }
                    >
                      {ui("common.remove")}
                    </button>
                    {prog.rating_max > 0 ? (
                      <label>
                        {ui("common.rating")}
                        <BoundedNumberInput
                          min={1}
                          max={prog.rating_max}
                          value={prog.rating}
                          onCommit={(n) =>
                            patch((cur) => ({
                              programs: editRow(cur.programs, prog.id, {
                                rating: n,
                              }),
                            }))
                          }
                        />
                      </label>
                    ) : null}
                    <RowNotes
                      ch={ch}
                      bucket="programs"
                      id={prog.id}
                      of={tr(prog.name)}
                      ui={ui}
                      patch={patch}
                    />
                  </div>
                ))}
              <AddonSelect
                rowName={tr(item.name)}
                prompt={ui("gear.addProgram")}
                tr={tr}
                options={byBook(catalog.programs || []).filter(
                  (prog) =>
                    prog.program_host === "cyberdecks" &&
                    !(d.programs || []).some(
                      (row) => row.parent_id === item.id && row.gear_id === prog.id,
                    ),
                )}
                onAdd={(prog) =>
                  patch((cur) => ({
                    programs: [
                      ...(cur.programs || []),
                      {
                        gear_id: prog.id,
                        rating: Math.max(1, prog.minrating || 1),
                        parent_id: item.id,
                        running: false,
                      },
                    ],
                  }))
                }
              />
              <AppRows
                hostId={item.id}
                hostName={item.name}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
              <DeckModuleRows
                hostId={item.id}
                hostName={tr(item.name)}
                used={item.module_used ?? 0}
                max={item.module_max ?? 1}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
              <MatrixModRows
                hostId={item.id}
                hostName={tr(item.name)}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
              <RowNotes
                ch={ch}
                bucket="cyberdecks"
                id={item.id}
                of={tr(item.name)}
                ui={ui}
                patch={patch}
              />
            </div>
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  cyberdecks: (ch.cyberdecks || []).filter((row) => row.id !== item.id),
                  programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                  apps: (ch.apps || []).filter((row) => row.parent_id !== item.id),
                  gear: dropTree(ch.gear || [], item.id),
                })
              }
            >
              {ui("common.delete")}
            </button>
          </div>
        ))}
      </>

      <CatalogPicker
        items={catalog.cyberdecks || []}
        label={ui("gear.searchCyberdeck")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating}
            {item.attributearray ? ` / ${item.attributearray}` : ""}
            {ui("gear.deckProgramLimit", { count: item.programs ?? "" })} / {item.cost}¥ /{" "}
            {item.avail || "-"} / {sourceBit(item, ui)}
          </>
        )}
        onAdd={(item) =>
          patch({
            cyberdecks: [
              ...(ch.cyberdecks || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
