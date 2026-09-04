"use client";

import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { lifeIncrement } from "@/lib/character/format";
import type { GearKind } from "@/lib/character/constants";
import type { MsgKey } from "@/lib/i18n";
import { ArmorGear } from "@/components/character/tabs/gear/ArmorGear";
import { WeaponGear } from "@/components/character/tabs/gear/WeaponGear";
import { CommlinkGear } from "@/components/character/tabs/gear/CommlinkGear";
import { CyberdeckGear } from "@/components/character/tabs/gear/CyberdeckGear";
import { RccGear } from "@/components/character/tabs/gear/RccGear";
import { OpticsGear } from "@/components/character/tabs/gear/OpticsGear";
import { SensorGear } from "@/components/character/tabs/gear/SensorGear";
import { VehicleDroneGear } from "@/components/character/tabs/gear/VehicleDroneGear";
import { MiscDrugsGear } from "@/components/character/tabs/gear/MiscDrugsGear";
import { LifestyleGear } from "@/components/character/tabs/gear/LifestyleGear";

// A module constant cannot call the hook, so it holds keys and the render
// resolves them.
const KIND_TABS: { kind: GearKind; label: MsgKey }[] = [
  { kind: "armor", label: "gear.kind.armor" },
  { kind: "weapon", label: "gear.kind.weapon" },
  { kind: "commlink", label: "gear.kind.commlink" },
  { kind: "cyberdeck", label: "gear.kind.cyberdeck" },
  { kind: "rcc", label: "gear.kind.rcc" },
  { kind: "optics", label: "gear.kind.optics" },
  { kind: "sensor", label: "gear.kind.sensor" },
  { kind: "vehicle", label: "gear.kind.vehicle" },
  { kind: "drone", label: "gear.kind.drone" },
  { kind: "misc", label: "gear.kind.misc" },
  { kind: "drugs", label: "gear.kind.drugs" },
  { kind: "lifestyle", label: "gear.kind.lifestyle" },
];

export function GearTab(props: TabPanelProps) {
  const { d, tr, ui } = props;
  const [gearKind, setGearKind] = useState<GearKind>("armor");

  return (
    <div className="card">
      <p className="muted">
        {d.career || false ? ui("gear.careerBuy") : ui("gear.chargenBuy")}
        {ui("gear.note", {
          spent: (d.nuyen_spent ?? 0).toLocaleString(),
          left: d.nuyen.toLocaleString(),
        })}
        {d.avail_limit == null
          ? ui("gear.availNone")
          : ui("gear.availLimit", { limit: d.avail_limit })}
        {d.worn_armor ? ui("gear.worn", { name: tr(d.worn_armor) }) : ""}
        {d.lifestyle
          ? ` ・ ${tr(d.lifestyle.name)} ${d.lifestyle.months}${lifeIncrement(d.lifestyle.increment)}`
          : ""}
        {d.commlink ? ` ・ ${tr(d.commlink.name)} DR${d.commlink.device_rating}` : ""}
        {d.cyberdeck ? ` ・ ${tr(d.cyberdeck.name)} DR${d.cyberdeck.device_rating}` : ""}
        {d.rcc ? ` ・ ${tr(d.rcc.name)} DR${d.rcc.device_rating}` : ""}
      </p>
      <div className="option-row">
        {KIND_TABS.map(({ kind, label }) => (
          <button
            key={kind}
            className={`tab ${gearKind === kind ? "active" : ""}`}
            onClick={() => setGearKind(kind)}
          >
            {ui(label)}
          </button>
        ))}
      </div>

      {gearKind === "armor" && <ArmorGear {...props} />}
      {gearKind === "weapon" && <WeaponGear {...props} />}
      {gearKind === "commlink" && <CommlinkGear {...props} />}
      {gearKind === "cyberdeck" && <CyberdeckGear {...props} />}
      {gearKind === "rcc" && <RccGear {...props} />}
      {gearKind === "optics" && <OpticsGear {...props} />}
      {gearKind === "sensor" && <SensorGear {...props} />}
      {gearKind === "drone" && <VehicleDroneGear {...props} mode="drone" />}
      {gearKind === "vehicle" && <VehicleDroneGear {...props} mode="vehicle" />}
      {gearKind === "misc" && <MiscDrugsGear {...props} mode="misc" />}
      {gearKind === "drugs" && <MiscDrugsGear {...props} mode="drugs" />}
      {gearKind === "lifestyle" && <LifestyleGear {...props} />}
    </div>
  );
}
