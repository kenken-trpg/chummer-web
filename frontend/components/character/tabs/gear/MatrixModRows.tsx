"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { DeckModuleRows } from "./DeckModuleRows";
import { ConstructionRecordEditor } from "./ConstructionRecordEditor";
import { ElectronicPartsPanel } from "./ElectronicPartsPanel";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import type { GearCatalogItem } from "@/lib/types";
import { dropTree } from "@/lib/character/gear";

/**
 * The Electronic Modifications (DT p.66) soldered into one matrix device.
 *
 * A commlink, a cyberdeck and an RCC all take them. Parts are separate: what
 * they cost is the point they move — Increase Attack buys Attack and two
 * boxes of the device's matrix condition monitor, and on a deck a
 * "Modify Matrix Attribute" trades one array slot against another. The three
 * device tabs are otherwise unalike enough that only this block is shared.
 */
export function MatrixModRows({
  hostId,
  hostName,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  hostId: string;
  hostName: string;
}) {
  const installed = (d.gear || []).filter(
    (row) => row.parent_id === hostId && row.category !== "Cyberdeck Modules",
  );
  const parentMod = (d.gear || []).find((r) => r.id === hostId);
  const host = [...(d.cyberdecks || []), ...(d.commlinks || []), ...(d.rccs || [])].find(
    (r) => r.id === hostId,
  );
  const preview = (mod: GearCatalogItem) => {
    if (mod.electronic_rule === "module" || mod.electronic_rule === "persona") return 2;
    if (mod.electronic_rule === "modify") return 4;
    if (mod.electronic_rule === "add")
      return (host?.construction_attributes?.device_rating || 0) * 2;
    if (mod.electronic_rule === "increase") {
      if (parentMod) return 4;
      const key = mod.electronic_attribute as "attack" | "sleaze" | "dataprocessing" | "firewall";
      return ((host?.construction_attributes?.[key] || 0) + 1) * 2;
    }
    return null;
  };
  return (
    <>
      <p className="muted">{ui("gear.constructionHelp")}</p>
      <ElectronicPartsPanel catalog={catalog} character={ch} d={d} tr={tr} ui={ui} patch={patch} />
      {installed.map((mod) => (
        <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
          <HelpTip
            label={ui("help.open", { label: tr(mod.label || mod.name) })}
            lines={[
              { label: ui("help.matrixmod.what") },
              { label: ui("help.matrixmod.array") },
              { label: ui("help.matrixmod.included") },
            ]}
          >
            {ui("help.matrixmod.statsLabel")}
          </HelpTip>{" "}
          {tr(mod.label || mod.name)}
          {mod.included ? ` / ${ui("common.included")}` : ` / ${mod.nuyen.toLocaleString()}¥`}{" "}
          {mod.category === "Electronic Modification" ? (
            <ConstructionRecordEditor
              mod={mod}
              character={ch}
              d={d}
              tr={tr}
              ui={ui}
              patch={patch}
            />
          ) : null}
          {mod.gear_id === "d6802ad9-5dca-434a-bc92-bf8a17a8c5dc" ? (
            <DeckModuleRows
              hostId={mod.id}
              hostName={tr(mod.name)}
              hardwired
              used={(d.gear || [])
                .filter((r) => r.category === "Cyberdeck Modules" && r.parent_id === mod.id)
                .reduce((n, r) => n + r.qty, 0)}
              max={mod.modification_valid ? 1 : 0}
              catalog={catalog}
              character={ch}
              d={d}
              tr={tr}
              ui={ui}
              patch={patch}
            />
          ) : null}
          {[
            "f860ec1a-b688-4975-95f4-4c11648b04f0",
            "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0",
          ].includes(mod.gear_id) ? (
            <MatrixModRows
              hostId={mod.id}
              hostName={tr(mod.name)}
              catalog={catalog}
              character={ch}
              d={d}
              tr={tr}
              ui={ui}
              patch={patch}
            />
          ) : null}
          <button
            className="btn danger"
            aria-label={ui("common.removeLabel", { name: tr(mod.label || mod.name) })}
            onClick={() => patch({ gear: dropTree(ch.gear || [], mod.id) })}
          >
            {ui("common.remove")}
          </button>
        </div>
      ))}
      <AddonSelect
        rowName={hostName}
        prompt={ui("gear.addModification")}
        tr={tr}
        optionLabel={(mod) =>
          `${tr(mod.name)} (${mod.cost}¥) / ${preview(mod) == null ? ui("gear.materialsUnsupported") : ui("gear.materialsCount", { required: preview(mod)!, allocated: 0, available: (d.gear || []).reduce((n, r) => n + (r.parts_available_units || 0) / 4, 0) })}`
        }
        options={(catalog.gear || []).filter(
          (mod) =>
            mod.category === "Electronic Modification" &&
            !installed.some((row) => row.gear_id === mod.id) &&
            (!parentMod ||
              (mod.electronic_rule === "increase" &&
                mod.electronic_attribute ===
                  (parentMod.gear_id === "f860ec1a-b688-4975-95f4-4c11648b04f0"
                    ? "attack"
                    : "sleaze"))),
        )}
        onAdd={(mod) =>
          patch({
            gear: [
              ...(ch.gear || []),
              { gear_id: mod.id, rating: Math.max(1, mod.minrating || 1), parent_id: hostId },
            ],
          })
        }
      />
    </>
  );
}
