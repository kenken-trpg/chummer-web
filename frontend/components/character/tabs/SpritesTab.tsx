"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { optionalNumber, testLine } from "@/lib/character/format";

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
              {item.name} / {item.registered ? ui("sprite.registered") : ui("sprite.compiled")} / L
              {item.level} / {ui("sprite.tasks")} {item.services}
              {item.registered ? "" : ui("sprite.untilReboot")}
              {" / "}
              {item.source}
            </div>
            {item.test ? <div className="muted">{testLine(item.test, "フェード")}</div> : null}
            {item.matrix ? (
              <div className="muted">
                ATK {item.matrix.attack} ・ SLZ {item.matrix.sleaze} ・ DP{" "}
                {item.matrix.dataprocessing} ・ FW {item.matrix.firewall} ・ INI{" "}
                {item.matrix.initiative}
              </div>
            ) : null}
            {item.powers?.length ? (
              <div className="muted">
                {ui("common.powers", {
                  list: item.powers.map((name) => tr(name)).join(ui("common.termSep")),
                })}
              </div>
            ) : null}
            <div className="cyber-controls">
              <label>
                Level
                <input
                  type="number"
                  min={1}
                  max={item.level_max}
                  value={item.level}
                  onChange={(e) =>
                    patch({
                      sprites: (ch.sprites || []).map((row) =>
                        row.id === item.id ? { ...row, level: Number(e.target.value) } : row,
                      ),
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
                      sprites: (ch.sprites || []).map((row) =>
                        row.id === item.id
                          ? {
                              ...row,
                              services: Number(e.target.value),
                              hits: null,
                              opposed_hits: null,
                            }
                          : row,
                      ),
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
                      sprites: (ch.sprites || []).map((row) =>
                        row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row,
                      ),
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
                      sprites: (ch.sprites || []).map((row) =>
                        row.id === item.id
                          ? { ...row, opposed_hits: optionalNumber(e.target.value) }
                          : row,
                      ),
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
                      sprites: (ch.sprites || []).map((row) =>
                        row.id === item.id
                          ? { ...row, registered: e.target.value === "registered" }
                          : row,
                      ),
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
        {(catalog.sprites || [])
          .filter((item) => {
            const q = spriteSearch.trim().toLowerCase();
            if (q)
              return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
            return item.source === "SR5";
          })
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {item.source}
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
          ))}
      </div>
    </div>
  );
}
