import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarFlags({ d, ui }: SidebarBlockProps) {
  return (
    <>
      {d.ambidextrous ? (
        <div className="stat">
          <span>{ui("side.handedness")}</span>
          <b>{ui("side.ambidextrous")}</b>
        </div>
      ) : null}
      {d.erased ? (
        <div className="stat">
          <span>{ui("side.identity")}</span>
          <b>{ui("side.erased")}</b>
        </div>
      ) : null}
      {d.excon ? (
        <div className="stat">
          <span>{ui("side.background")}</span>
          <b>Ex-Con</b>
        </div>
      ) : null}
      {d.overclocker ? (
        <div className="stat">
          <span>{ui("side.overclock")}</span>
          <b>{ui("side.overclockValue")}</b>
        </div>
      ) : null}
      {(d.special_modification_limit?.max || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.specialMod")}</span>
          <b>
            {d.special_modification_limit?.used || 0} / {d.special_modification_limit?.max}
          </b>
        </div>
      ) : null}
      {d.friends_in_high_places ? (
        <div className="stat">
          <span>{ui("side.contacts")}</span>
          <b>FiHP</b>
        </div>
      ) : null}
      {d.made_man ? (
        <div className="stat">
          <span>{ui("side.org")}</span>
          <b>Made Man</b>
        </div>
      ) : null}
      {(d.trustfund || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.trust")}</span>
          <b>
            TF{d.trustfund}
            {d.trustfund_label ? `（${d.trustfund_label}）` : ""}
          </b>
        </div>
      ) : null}
      {(d.dealer_connection_categories || []).length ? (
        <div className="stat">
          <span>{ui("side.dealer")}</span>
          <b>{(d.dealer_connection_categories || []).join(", ")} −10%</b>
        </div>
      ) : null}
    </>
  );
}
