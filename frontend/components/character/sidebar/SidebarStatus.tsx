import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { limitModifierLine, specialArmorBits } from "@/lib/character/format";

export function SidebarStatus({ ch, d, tr, career, error, ui }: SidebarBlockProps) {
  return (
    <>
      <h2>{ch.name}</h2>
      <div className="muted">
        {tr(ch.metatype)}
        {ch.metavariant ? ` / ${tr(ch.metavariant)}` : ""} ・ {ch.talent}
      </div>
      <div className="stat">
        <span>{ui("side.mode")}</span>
        <b>{career ? ui("side.mode.career") : ui("side.mode.chargen")}</b>
      </div>
      <div className="stat">
        <span>{ui("side.buildMethod")}</span>
        <b>
          {(ch.build_method || "Priority") === "Karma"
            ? `Karma ${d.karma.remaining}/${d.karma.pool}`
            : (ch.build_method || "Priority") === "SumToTen"
              ? `Sum to Ten ${d.sum_to_ten?.used ?? 0}/${d.sum_to_ten?.max ?? 10}`
              : "Priority"}
        </b>
      </div>
      {error ? <p className="errors">{error}</p> : null}
      {d.errors.length ? (
        <ul className="errors">
          {d.errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      ) : (
        // `errors` / `warnings` themselves come from the engine, in Japanese.
        // Translating those means translating the backend's messages too — see
        // docs/i18n.md.
        <p className="ok">{career ? ui("side.ok.career") : ui("side.ok.chargen")}</p>
      )}
      {(d.warnings || []).length ? (
        <ul className="warn">
          {d.warnings!.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}
      <div className="stat">
        <span>{ui("side.limits")}</span>
        <b>
          {d.limits.physical}/{d.limits.mental}/{d.limits.social}
        </b>
      </div>
      {(d.limit_modifiers || []).map((mod, idx) => (
        <div className="stat" key={`${mod.limit}-${mod.condition || ""}-${idx}`}>
          <span>{limitModifierLine([mod])}</span>
        </div>
      ))}
      <div className="stat">
        <span>{ui("side.condition")}</span>
        <b>
          P{d.condition_monitor.physical} / S{d.condition_monitor.stun}
        </b>
      </div>
      {d.limb_quality ? (
        <div className="stat">
          <span>{ui("side.limbQuality")}</span>
          <b>
            {ui("side.limbQualityValue", {
              count: d.limb_quality.count,
              pairs: d.limb_quality.pairs,
            })}
          </b>
        </div>
      ) : null}
      <div className="stat">
        <span>{ui("side.initiative")}</span>
        <b>
          {d.initiative.value}+{d.initiative.dice}d6
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.armor")}</span>
        <b>
          {d.armor}
          {d.worn_armor ? `（${tr(d.worn_armor)}）` : ""}
        </b>
      </div>
      {specialArmorBits(d.special_armor).map((row) => (
        <div className="stat" key={row.label}>
          <span>{row.label}</span>
          <b>{row.value}</b>
        </div>
      ))}
      {(d.reach || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.reach")}</span>
          <b>+{d.reach}</b>
        </div>
      ) : null}
      {(d.lifestyle_cost_mod || 0) !== 0 ? (
        <div className="stat">
          <span>{ui("side.lifestyleCost")}</span>
          <b>
            {d.lifestyle_cost_mod! > 0 ? "+" : ""}
            {d.lifestyle_cost_mod}%
          </b>
        </div>
      ) : null}
      {(d.notoriety || 0) !== 0 || career ? (
        <div className="stat">
          <span>{ui("side.notoriety")}</span>
          <b>
            {(d.notoriety || 0) > 0 ? "+" : ""}
            {d.notoriety || 0}
          </b>
        </div>
      ) : null}
      {(d.fame || 0) !== 0 ? (
        <div className="stat">
          <span>{ui("side.fame")}</span>
          <b>
            {d.fame! > 0 ? "+" : ""}
            {d.fame}
          </b>
        </div>
      ) : null}
      {career || (d.street_cred || 0) > 0 || (d.public_awareness || 0) > 0 ? (
        <>
          <div className="stat">
            <span>{ui("side.streetCred")}</span>
            <b>{d.street_cred || 0}</b>
          </div>
          <div className="stat">
            <span>{ui("side.publicAwareness")}</span>
            <b>{d.public_awareness || 0}</b>
          </div>
        </>
      ) : (d.public_awareness || 0) !== 0 ? (
        <div className="stat">
          <span>{ui("side.publicAwareness")}</span>
          <b>
            {d.public_awareness! > 0 ? "+" : ""}
            {d.public_awareness}
          </b>
        </div>
      ) : null}
    </>
  );
}
