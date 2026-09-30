import { HelpTip } from "@/components/help/HelpTip";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { renderNotice } from "@/lib/engine-notices";

export function SidebarFlags({ d, ui }: SidebarBlockProps) {
  return (
    <>
      {d.ambidextrous ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.handedness") })}
              lines={[{ label: ui("help.flag.ambidextrous") }]}
            >
              {ui("side.handedness")}
            </HelpTip>
          </span>
          <b>{ui("side.ambidextrous")}</b>
        </div>
      ) : null}
      {d.erased ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.identity") })}
              lines={[{ label: ui("help.flag.erased") }]}
            >
              {ui("side.identity")}
            </HelpTip>
          </span>
          <b>{ui("side.erased")}</b>
        </div>
      ) : null}
      {d.excon ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.background") })}
              lines={[{ label: ui("help.flag.excon") }]}
            >
              {ui("side.background")}
            </HelpTip>
          </span>
          <b>Ex-Con</b>
        </div>
      ) : null}
      {d.overclocker ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.overclock") })}
              lines={[{ label: ui("help.flag.overclock") }]}
            >
              {ui("side.overclock")}
            </HelpTip>
          </span>
          <b>{ui("side.overclockValue")}</b>
        </div>
      ) : null}
      {(d.special_modification_limit?.max || 0) > 0 ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.specialMod") })}
              lines={[{ label: ui("help.flag.specialMod") }]}
            >
              {ui("side.specialMod")}
            </HelpTip>
          </span>
          <b>
            {d.special_modification_limit?.used || 0} / {d.special_modification_limit?.max}
          </b>
        </div>
      ) : null}
      {d.friends_in_high_places ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.contacts") })}
              lines={[{ label: ui("help.flag.fihp") }]}
            >
              {ui("side.contacts")}
            </HelpTip>
          </span>
          <b>FiHP</b>
        </div>
      ) : null}
      {d.made_man ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.org") })}
              lines={[{ label: ui("help.flag.madeMan") }]}
            >
              {ui("side.org")}
            </HelpTip>
          </span>
          <b>Made Man</b>
        </div>
      ) : null}
      {(d.trustfund || 0) > 0 ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.trust") })}
              lines={[{ label: ui("help.flag.trustfund") }]}
            >
              {ui("side.trust")}
            </HelpTip>
          </span>
          <b>
            TF{d.trustfund}
            {d.trustfund_label ? `（${renderNotice(d.trustfund_label, ui)}）` : ""}
          </b>
        </div>
      ) : null}
      {(d.dealer_connection_categories || []).length ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.dealer") })}
              lines={[{ label: ui("help.flag.dealer") }]}
            >
              {ui("side.dealer")}
            </HelpTip>
          </span>
          <b>{(d.dealer_connection_categories || []).join(", ")} −10%</b>
        </div>
      ) : null}
    </>
  );
}
