"use client";
import { useState } from "react";
import { CustomDrugMixer } from "@/components/character/tabs/gear/CustomDrugMixer";
import { AddictionTests } from "@/components/character/tabs/gear/misc/AddictionTests";
import { MiscGearPicker } from "@/components/character/tabs/gear/misc/MiscGearPicker";
import { MiscGearRow } from "@/components/character/tabs/gear/misc/MiscGearRow";
import type { TabPanelProps } from "@/components/character/types";
import { isDrugCategory } from "@/lib/character/constants";

export function MiscDrugsGear(props: TabPanelProps & { mode: "misc" | "drugs" }) {
  const { catalog, character: ch, d, tr, ui, patch, mode } = props;
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

  return (
    <>
      {mode === "drugs" ? <AddictionTests d={d} ui={ui} /> : null}
      <>
        {(d.gear || [])
          .filter((item) => {
            if (item.parent_id) return false;
            const drugCat = isDrugCategory(item);
            return mode === "drugs" ? drugCat : !drugCat;
          })
          .map((item) => (
            <MiscGearRow
              key={item.id}
              item={item}
              catalog={catalog}
              character={ch}
              d={d}
              tr={tr}
              ui={ui}
              patch={patch}
              slotPick={slotPick}
              setSlotPick={setSlotPick}
              extraPick={extraPick}
              setExtraPick={setExtraPick}
              mode={mode}
              gearSearch={gearSearch}
            />
          ))}
      </>

      {mode === "drugs" ? <CustomDrugMixer {...props} /> : null}

      <MiscGearPicker
        catalog={catalog}
        character={ch}
        tr={tr}
        ui={ui}
        patch={patch}
        mode={mode}
        gearSearch={gearSearch}
        setGearSearch={setGearSearch}
        gearCat={gearCat}
        setGearCat={setGearCat}
        extraPick={extraPick}
        setExtraPick={setExtraPick}
      />
    </>
  );
}
