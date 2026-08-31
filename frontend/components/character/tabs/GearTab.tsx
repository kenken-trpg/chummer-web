"use client";

import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { lifeIncrement } from "@/lib/character/format";
import type { GearKind } from "@/lib/character/constants";
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

const KIND_TABS: { kind: GearKind; label: string }[] = [
  { kind: "armor", label: "防具" },
  { kind: "weapon", label: "武器" },
  { kind: "commlink", label: "通信機" },
  { kind: "cyberdeck", label: "サイバーデッキ" },
  { kind: "rcc", label: "RCC" },
  { kind: "optics", label: "視覚／聴覚" },
  { kind: "sensor", label: "センサー" },
  { kind: "vehicle", label: "車両" },
  { kind: "drone", label: "ドローン" },
  { kind: "misc", label: "ギア" },
  { kind: "drugs", label: "ドラッグ" },
  { kind: "lifestyle", label: "ライフスタイル" },
];

export function GearTab(props: TabPanelProps) {
  const { d, tr } = props;
  const [gearKind, setGearKind] = useState<GearKind>("armor");

  return (
    <div className="card">
      <p className="muted">
        {d.career || false ? "キャリアの買い物" : "作成時の購入"}
        。防具は装備中の本体1着＋ヘルメット等の加算、ウェア装甲と合算。消費{" "}
        {(d.nuyen_spent ?? 0).toLocaleString()}¥{" ・ "}残 {d.nuyen.toLocaleString()}¥
        {d.avail_limit == null ? " ・ 入手制限なし" : ` ・ 入手≤${d.avail_limit}`}
        {d.worn_armor ? ` ・ 装備 ${tr(d.worn_armor)}` : ""}
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
            {label}
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
