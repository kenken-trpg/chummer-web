"use client";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { optionalNumber, sourceBit, testLine } from "@/lib/character/format";
import { CritterPowerRow } from "@/components/character/CritterPowerRow";
import { HelpTip } from "@/components/help/HelpTip";
import { editRow } from "@/lib/character/rows";

export function SpritesTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [spriteSearch, setSpriteSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        {ui("sprite.note")}
        {d.fade_resist
          ? ui("res.fadeResist", { attrs: d.fade_resist.attrs, pool: d.fade_resist.pool })
          : ""}
        {d.living_persona
          ? ui("sprite.livingPersona", {
              dr: d.living_persona.device_rating,
              atk: d.living_persona.attack,
              slz: d.living_persona.sleaze,
              dp: d.living_persona.dataprocessing,
              fw: d.living_persona.firewall,
            })
          : ""}
      </p>
      {(d.sprites || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              <HelpTip
                label={ui("help.open", { label: tr(item.name) })}
                lines={[
                  { label: ui("help.sprite.level") },
                  { label: ui("help.sprite.tasks") },
                  { label: ui("help.sprite.registered") },
                ]}
              >
                {ui("help.sprite.statsLabel")}
              </HelpTip>{" "}
              {item.name} / {item.registered ? ui("sprite.registered") : ui("sprite.compiled")} / L
              {item.level} / {ui("sprite.tasks")} {item.services}
              {item.registered ? "" : ui("sprite.untilReboot")}
              {" / "}
              {sourceBit(item, ui)}
            </div>
            {item.test ? <div className="muted">{testLine(item.test, ui, "fmt.fade")}</div> : null}
            {item.matrix ? (
              <div className="muted">
                ATK {item.matrix.attack} ・ SLZ {item.matrix.sleaze} ・ DP{" "}
                {item.matrix.dataprocessing} ・ FW {item.matrix.firewall} ・ INI{" "}
                {item.matrix.initiative}
              </div>
            ) : null}
            {item.powers?.length ? (
              <div className="muted">
                {ui("common.powersHead")}
                <ul className="critter-powers">
                  {item.powers.map((power) => (
                    <li key={power.name}>
                      <CritterPowerRow power={power} tr={tr} ui={ui} />
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="cyber-controls">
              <label>
                {ui("common.level")}
                <input
                  type="number"
                  min={1}
                  max={item.level_max}
                  value={item.level}
                  onChange={(e) =>
                    patch({
                      sprites: editRow(ch.sprites, item.id, { level: Number(e.target.value) }),
                    })
                  }
                />
              </label>
              <label>
                {ui("sprite.tasks")}
                <input
                  type="number"
                  min={0}
                  max={item.level_max}
                  value={item.services}
                  onChange={(e) =>
                    patch({
                      sprites: editRow(ch.sprites, item.id, {
                        services: Number(e.target.value),
                        hits: null,
                        opposed_hits: null,
                      }),
                    })
                  }
                />
              </label>
              <label>
                {ui("common.hits", {
                  kind: item.registered ? ui("sprite.registered") : ui("sprite.compiled"),
                })}
                <input
                  type="number"
                  min={0}
                  value={item.hits ?? ""}
                  onChange={(e) =>
                    patch({
                      sprites: editRow(ch.sprites, item.id, {
                        hits: optionalNumber(e.target.value),
                      }),
                    })
                  }
                />
              </label>
              <label>
                {ui("sprite.spriteHits")}
                <input
                  type="number"
                  min={0}
                  value={item.opposed_hits ?? ""}
                  onChange={(e) =>
                    patch({
                      sprites: editRow(ch.sprites, item.id, {
                        opposed_hits: optionalNumber(e.target.value),
                      }),
                    })
                  }
                />
              </label>
              <label>
                {ui("common.kind")}
                <select
                  value={item.registered ? "registered" : "compiled"}
                  onChange={(e) =>
                    patch({
                      sprites: editRow(ch.sprites, item.id, {
                        registered: e.target.value === "registered",
                      }),
                    })
                  }
                >
                  <option value="compiled">{ui("sprite.compiled")}</option>
                  <option value="registered">{ui("sprite.registered")}</option>
                </select>
              </label>
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                sprites: (ch.sprites || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("sprite.search")}
        aria-label={ui("sprite.search")}
        value={spriteSearch}
        onChange={(e) => setSpriteSearch(e.target.value)}
      />
      <div className="quality-list">
        {/* Through `<PickerList>` so the settings' book list reaches this one
            too: it listed SR5 sprites until you typed, and every book's after
            that, which is the wrong way round. */}
        <PickerList
          items={(catalog.sprites || []).filter((item) => {
            const q = spriteSearch.trim().toLowerCase();
            return (
              !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
            );
          })}
        >
          {(item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {sourceBit(item, ui)}
                </div>
              </div>
              <div>
                <button
                  className="btn"
                  onClick={() =>
                    patch({
                      sprites: [
                        ...(ch.sprites || []),
                        { sprite_id: item.id, level: 1, registered: false },
                      ],
                    })
                  }
                >
                  {ui("sprite.compiled")}
                </button>{" "}
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      sprites: [
                        ...(ch.sprites || []),
                        { sprite_id: item.id, level: 1, registered: true },
                      ],
                    })
                  }
                >
                  {ui("sprite.registered")}
                </button>
              </div>
            </div>
          )}
        </PickerList>
      </div>
    </div>
  );
}
