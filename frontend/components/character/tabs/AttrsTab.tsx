"use client";

import type { TabPanelProps } from "@/components/character/types";

import { ATTRS, ATTR_JA } from "@/lib/character/constants";

export function AttrsTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const spec = d.metatype_info.attributes;

  return (
          <div className="card">
            {ATTRS.map((key) => {
              const hidden = (key === "MAG" && !d.enabled_tabs.includes("MAG")) || (key === "RES" && !d.enabled_tabs.includes("RES"));
              if (hidden) return null;
              const range = spec[key] || { min: 1, max: 6, aug: 6 };
              return (
                <div className="attr-row" key={key}>
                  <span>{ATTR_JA[key]}</span>
                  <input
                    type="range"
                    min={range.min}
                    max={range.max}
                    value={ch.attributes[key] ?? range.min}
                    onChange={(e) => {
                      const attributes = { ...ch.attributes, [key]: Number(e.target.value) };
                      setCharacter({ ...ch, attributes });
                    }}
                    onMouseUp={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onTouchEnd={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onBlur={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                  />
                  <b>
                    {d.totals[key]} <span className="muted">/{range.max}</span>
                    {(d.ware_attr_bonus?.[key] || 0) !== 0 ? (
                      <span className="muted"> ウェア+{d.ware_attr_bonus![key]}</span>
                    ) : null}
                    {d.limb_replace && (key === "STR" || key === "AGI") ? (
                      <span className="muted"> 肉{key === "STR" ? d.limb_replace.meat_str : d.limb_replace.meat_agi}</span>
                    ) : null}
                  </b>
                </div>
              );
            })}
            <p className="muted">属性点 {d.points.attributes.used}/{d.points.attributes.max} ・ 特殊点 {d.points.special.used}/{d.points.special.max}</p>
          </div>

  );
}
