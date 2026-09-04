import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { lifeIncrement, wareAttrLine } from "@/lib/character/format";

export function SidebarEconomy({ d, tr, ui }: SidebarBlockProps) {
  /** "programs 2/5" hangs off both the deck and the RCC. */
  const programs = (used: number | undefined, max: number | undefined) =>
    max ? ` / ${ui("side.programs", { used: used ?? 0, max })}` : "";

  return (
    <>
      <div className="stat">
        <span>{ui("common.nuyen")}</span>
        <b>{d.nuyen.toLocaleString()}¥</b>
      </div>
      <div className="stat">
        <span>{ui("side.availLimit")}</span>
        <b>{d.avail_limit == null ? ui("side.availNone") : d.avail_limit}</b>
      </div>
      <div className="stat">
        <span>{ui("side.deviceRating")}</span>
        <b>{d.device_rating_limit ?? 6}</b>
      </div>
      {d.skillwires ? (
        <div className="stat">
          <span>{ui("side.skillwires")}</span>
          <b>R{d.skillwires}</b>
        </div>
      ) : null}
      {d.skilljack ? (
        <div className="stat">
          <span>{ui("side.skilljack")}</span>
          <b>R{d.skilljack}</b>
        </div>
      ) : null}
      <div className="stat">
        <span>{ui("side.wareBoost")}</span>
        <b>
          {wareAttrLine(d.ware_attr_bonus)
            ? `${wareAttrLine(d.ware_attr_bonus)} / ${ui("side.wareBoostLimit", { max: d.ware_attr_limit ?? 4 })}`
            : `+${d.ware_attr_limit ?? 4}`}
        </b>
      </div>
      {d.lifestyle ? (
        <div className="stat">
          <span>{ui("side.lifestyle")}</span>
          <b>
            {tr(d.lifestyle.name)} {d.lifestyle.months}
            {lifeIncrement(d.lifestyle.increment, ui)}
          </b>
        </div>
      ) : null}
      {d.commlink ? (
        <div className="stat">
          <span>{ui("side.commlink")}</span>
          <b>
            {tr(d.commlink.name)} DR{d.commlink.device_rating}
          </b>
        </div>
      ) : null}
      {d.cyberdeck ? (
        <div className="stat">
          <span>{ui("side.cyberdeck")}</span>
          <b>
            {tr(d.cyberdeck.name)} DR{d.cyberdeck.device_rating} / {d.cyberdeck.attack}/
            {d.cyberdeck.sleaze}/{d.cyberdeck.dataprocessing}/{d.cyberdeck.firewall}
            {programs(d.cyberdeck.program_used, d.cyberdeck.program_max)}
          </b>
        </div>
      ) : null}
      {d.rcc ? (
        <div className="stat">
          <span>RCC</span>
          <b>
            {tr(d.rcc.name)} DR{d.rcc.device_rating} / DP{d.rcc.dataprocessing} FW{d.rcc.firewall}
            {programs(d.rcc.program_used, d.rcc.program_max)}
          </b>
        </div>
      ) : null}
      {(d.optics || []).some((item) => !item.parent_id) ? (
        <div className="stat">
          <span>{ui("side.optics")}</span>
          <b>
            {ui("side.count", { count: (d.optics || []).filter((item) => !item.parent_id).length })}
          </b>
        </div>
      ) : null}
      {(d.sensors || []).some((item) => !item.parent_id) ? (
        <div className="stat">
          <span>{ui("side.sensors")}</span>
          <b>
            {ui("side.count", {
              count: (d.sensors || []).filter((item) => !item.parent_id).length,
            })}
          </b>
        </div>
      ) : null}
      {(d.drones || []).length ? (
        <div className="stat">
          <span>{ui("side.drones")}</span>
          <b>{ui("side.count", { count: (d.drones || []).length })}</b>
        </div>
      ) : null}
      <div className="stat">
        <span>{ui("side.karma")}</span>
        <b>
          {d.karma.remaining} / {d.karma.pool}
        </b>
      </div>
    </>
  );
}
