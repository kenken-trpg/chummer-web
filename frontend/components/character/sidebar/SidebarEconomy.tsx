import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { lifeIncrement, wareAttrLine } from "@/lib/character/format";

export function SidebarEconomy({ d, tr }: SidebarBlockProps) {
  return (
    <>
      <div className="stat">
        <span>ニューエン</span>
        <b>{d.nuyen.toLocaleString()}¥</b>
      </div>
      <div className="stat">
        <span>入手制限</span>
        <b>{d.avail_limit == null ? "制限なし" : d.avail_limit}</b>
      </div>
      <div className="stat">
        <span>デバイスレーティング</span>
        <b>{d.device_rating_limit ?? 6}</b>
      </div>
      {d.skillwires ? (
        <div className="stat">
          <span>スキルワイヤ</span>
          <b>R{d.skillwires}</b>
        </div>
      ) : null}
      {d.skilljack ? (
        <div className="stat">
          <span>スキルジャック</span>
          <b>R{d.skilljack}</b>
        </div>
      ) : null}
      <div className="stat">
        <span>ウェア強化</span>
        <b>
          {wareAttrLine(d.ware_attr_bonus)
            ? `${wareAttrLine(d.ware_attr_bonus)} / 上限+${d.ware_attr_limit ?? 4}`
            : `+${d.ware_attr_limit ?? 4}`}
        </b>
      </div>
      {d.lifestyle ? (
        <div className="stat">
          <span>ライフスタイル</span>
          <b>
            {tr(d.lifestyle.name)} {d.lifestyle.months}
            {lifeIncrement(d.lifestyle.increment)}
          </b>
        </div>
      ) : null}
      {d.commlink ? (
        <div className="stat">
          <span>通信機</span>
          <b>
            {tr(d.commlink.name)} DR{d.commlink.device_rating}
          </b>
        </div>
      ) : null}
      {d.cyberdeck ? (
        <div className="stat">
          <span>サイバーデッキ</span>
          <b>
            {tr(d.cyberdeck.name)} DR{d.cyberdeck.device_rating} / {d.cyberdeck.attack}/
            {d.cyberdeck.sleaze}/{d.cyberdeck.dataprocessing}/{d.cyberdeck.firewall}
            {d.cyberdeck.program_max
              ? ` / プログラム ${d.cyberdeck.program_used ?? 0}/${d.cyberdeck.program_max}`
              : ""}
          </b>
        </div>
      ) : null}
      {d.rcc ? (
        <div className="stat">
          <span>RCC</span>
          <b>
            {tr(d.rcc.name)} DR{d.rcc.device_rating} / DP{d.rcc.dataprocessing} FW{d.rcc.firewall}
            {d.rcc.program_max
              ? ` / プログラム ${d.rcc.program_used ?? 0}/${d.rcc.program_max}`
              : ""}
          </b>
        </div>
      ) : null}
      {(d.optics || []).some((item) => !item.parent_id) ? (
        <div className="stat">
          <span>視覚／聴覚</span>
          <b>{(d.optics || []).filter((item) => !item.parent_id).length}件</b>
        </div>
      ) : null}
      {(d.sensors || []).some((item) => !item.parent_id) ? (
        <div className="stat">
          <span>センサー</span>
          <b>{(d.sensors || []).filter((item) => !item.parent_id).length}件</b>
        </div>
      ) : null}
      {(d.drones || []).length ? (
        <div className="stat">
          <span>ドローン</span>
          <b>{(d.drones || []).length}件</b>
        </div>
      ) : null}
      <div className="stat">
        <span>カルマ</span>
        <b>
          {d.karma.remaining} / {d.karma.pool}
        </b>
      </div>
    </>
  );
}
