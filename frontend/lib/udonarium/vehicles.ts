/** Vehicles and drones, each as a piece of its own. */
import type { Catalog, Character, Derived, InstalledWeapon } from "@/lib/types";
import { attrName, makeT } from "@/lib/ui-strings";
import { type Locale } from "@/lib/i18n";
import { vehicleConditionMonitor, vehicleHandling, vehicleSkills } from "@/lib/vtt-pools";
import { woundTrack, Section, pieceXml, resource, uiFor, varName } from "./shared";

// --- vehicles and drones, as their own pieces ------------------------------
// A vehicle is driven three ways in SR5, and the dice change with each: by
// hand (Reaction + Pilot skill), remotely or jumped into (Logic in place of
// Reaction, SR5 p.265), and on its own (Pilot rating + autosoft, limited by
// Sensor rather than Handling, SR5 p.269). The piece carries all three,
// because which one applies is a question the table answers per scene.
//
// Handling, Sensor, Pilot, Armor and the skill that drives it are the
// variables. Everything else is a number: a vehicle's stats do not move
// mid-scene, but a Handling modifier, a swapped autosoft or a different
// rigger behind the wheel all do.

const VEHICLE_ATTRS = ["REA", "LOG", "AGI"] as const;

/**
 * One piece per vehicle or drone of `kind`.
 *
 * The piloting skill is a variable rather than a resolved number. Which skill
 * a vehicle wants is only half in the data — a car is `Cars` and clearly
 * ground, but Chummer files drones by size (`Drones: Medium`), which says
 * nothing about whether they roll, fly or walk. So every Pilot skill the
 * character has is defined, `{操縦技能}` starts at the best of them, and the
 * note says which one that was: switching is one line at the table.
 */
export function buildVehiclePieces(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
  kind: "vehicles" | "drones" = "drones",
): { name: string; xml: string }[] {
  const ui = uiFor(locale);
  const t = makeT(catalog, locale);
  const d: Derived = ch.derived;
  const A = (k: string) => varName(attrName(k, t));
  const at = (k: string) => d.totals?.[k] || 0;

  const { pilots, gunnery } = vehicleSkills(catalog);
  // the rating, not the pool: the attribute is its own variable in the rolls
  const rating = (name: string) => (d.skill_totals?.[name] || 0) + (d.skill_bonus?.[name] || 0);
  const trained = pilots.filter((name) => rating(name) > 0);
  const best = trained.reduce((a, b) => (rating(b) > rating(a) ? b : a), trained[0] || "");

  const vPilotSkill = varName(ui("udo.varPilotSkill"));
  const vGunnery = varName(ui("udo.varGunnery"));
  const vHandling = varName(ui("udo.varHandling"));
  const vOffroad = varName(ui("udo.varHandlingOffroad"));
  const vSensor = varName(ui("udo.varSensor"));
  const vPilot = varName(ui("udo.varPilot"));
  const vArmor = varName(ui("udo.varArmor"));
  const vBody = varName(ui("udo.varBody"));
  const vAutosoft = varName(ui("udo.varAutosoft"));

  return (d[kind] || []).map((v) => {
    const handling = vehicleHandling(v.handling);
    const pilot = Number.parseInt(String(v.pilot ?? ""), 10) || 0;
    const sensor = Number.parseInt(String(v.sensor ?? ""), 10) || 0;
    // the guns bolted into this one: the mount links to a weapon row of the
    // character, and `mounted_on` is the back-reference the engine sets
    const guns = (d.weapons || []).filter(
      (w) => w.mounted_on === v.id && w.modular_equipped !== false,
    );
    const implants = (d.weapons || []).filter((w) => w.vehicle_id === v.id);
    // an autosoft loaded into this one, whether the player put it there or
    // the drone's own entry brought it
    const autosofts = (d.programs || []).filter((p) => p.parent_id === v.id);
    const targeting = autosofts.reduce((a, p) => Math.max(a, p.rating || 0), 0);

    const gunInfo = (w: InstalledWeapon) => {
      const info = [
        w.damage && `DV${w.damage}`,
        w.ap && `AP${w.ap}`,
        w.mode && w.mode !== "0" ? w.mode : "",
      ]
        .filter(Boolean)
        .join("/");
      return `${tr(w.name)}${info ? ` [${info}]` : ""}`;
    };
    const acc = (w: InstalledWeapon) => {
      const n = String(w.accuracy || "").trim();
      return /^\d+$/.test(n) ? n : `{${vSensor}}`;
    };

    // one block per way of driving it, because the pool changes with each
    const byHand = new Section();
    byHand.roll(`({${A("REA")}}+{${vPilotSkill}}+0)B6@{${vHandling}}`, ui("udo.vehicleTest"));
    // anything that leaves the road has a second Handling, and the limit is
    // the only thing that changes with it
    if (handling.offroad !== null)
      byHand.roll(
        `({${A("REA")}}+{${vPilotSkill}}+0)B6@{${vOffroad}}`,
        ui("udo.vehicleTestOffroad"),
      );
    guns.forEach((w) =>
      byHand.roll(
        `({${A("AGI")}}+{${vGunnery}}+0)B6@${acc(w)}`,
        `${ui("udo.gunneryByHand")} ${gunInfo(w)}`,
      ),
    );

    // remote or jumped in: Logic takes Reaction's place (SR5 p.265)
    const rigged = new Section();
    rigged.roll(`({${A("LOG")}}+{${vPilotSkill}}+0)B6@{${vHandling}}`, ui("udo.vehicleTestRigged"));
    if (handling.offroad !== null)
      rigged.roll(
        `({${A("LOG")}}+{${vPilotSkill}}+0)B6@{${vOffroad}}`,
        ui("udo.vehicleTestRiggedOffroad"),
      );
    guns.forEach((w) =>
      rigged.roll(
        `({${A("LOG")}}+{${vGunnery}}+0)B6@${acc(w)}`,
        `${ui("udo.gunneryRigged")} ${gunInfo(w)}`,
      ),
    );

    // on its own, off the Pilot rating and an autosoft (SR5 p.269)
    const auto = new Section();
    auto.roll(`({${vPilot}}+{${vAutosoft}}+0)B6@{${vSensor}}`, ui("udo.vehicleTestPilot"));
    guns.forEach((w) =>
      auto.roll(
        `({${vPilot}}+{${vAutosoft}}+0)B6@{${vSensor}}`,
        `${ui("udo.gunneryPilot")} ${gunInfo(w)}`,
      ),
    );

    // the same either way it is driven
    const common = new Section();
    common.roll(`({${vBody}}+{${vArmor}}+0)B6`, ui("udo.damageResist"));
    // a vehicle's Device Rating is its Pilot rating — the game data carries no
    // separate one — so Matrix damage comes back off it twice over
    common.roll(`({${vPilot}}+{${vPilot}}+0)B6`, ui("coco.matrixResist"));

    const sec = new Section();
    sec.def(vHandling, handling.onroad);
    if (handling.offroad !== null) sec.def(vOffroad, handling.offroad);
    sec.def(vPilot, pilot);
    sec.def(vSensor, sensor);
    sec.def(vBody, Number.parseInt(String(v.body ?? ""), 10) || 0);
    sec.def(vArmor, Number.parseInt(String(v.armor ?? ""), 10) || 0);
    sec.def(vPilotSkill, best ? rating(best) : 0);
    // only where there is something to shoot with: an unarmed vehicle would
    // carry a Gunnery variable nothing reads
    if (guns.length) sec.def(vGunnery, gunnery ? rating(gunnery) : 0);
    sec.def(vAutosoft, targeting);
    for (const name of trained) if (name !== best) sec.def(varName(tr(name)), rating(name));
    for (const k of VEHICLE_ATTRS) {
      if (k === "AGI" && !guns.length) continue;
      sec.def(A(k), at(k));
    }

    const notes = [
      ui("udo.vehicleName", {
        name: tr(v.name),
        category: tr(v.category || ""),
        speed: v.speed,
        accel: v.accel,
      }),
      best ? ui("udo.pilotSkillFrom", { skill: tr(best) }) : ui("udo.pilotSkillNone"),
      autosofts.length
        ? ui("udo.autosoftsLoaded", {
            list: autosofts.map((p) => p.label || tr(p.name)).join(ui("common.listSep")),
          })
        : ui("udo.autosoftsNone"),
      implants.length
        ? ui("weapon.vehicleInventory", { list: implants.map(gunInfo).join(ui("common.listSep")) })
        : "",
      ui("udo.vehicleNote"),
    ].filter(Boolean);

    const cm = vehicleConditionMonitor(v.body);
    const matrixCm = 8 + Math.ceil(Math.max(pilot, 1) / 2);
    const name = tr(v.name);
    return {
      name,
      xml: pieceXml({
        name,
        buffLabel: ui("udo.panelBuff"),
        palette: [
          notes.join("\n"),
          byHand.text(ui("udo.secVehicleByHand")),
          rigged.text(ui("udo.secVehicleRigged")),
          auto.text(ui("udo.secVehiclePilot")),
          common.text(ui("udo.secDefense")),
          sec.text(),
        ]
          .filter(Boolean)
          .join("\n\n"),
        panels: [
          {
            title: ui("udo.panelStatus"),
            rows: [
              resource(ui("coco.initiative"), 0, 0),
              resource(ui("udo.varSensor"), sensor, sensor),
              resource(ui("udo.varPilot"), pilot, pilot),
            ],
          },
          {
            title: ui("udo.panelCm"),
            rows: [
              resource(ui("coco.cmPhysical"), 0, cm),
              resource(ui("coco.cmMatrix"), 0, matrixCm),
              woundTrack(ui, cm, 0),
            ],
          },
        ],
      }),
    };
  });
}

/**
 * The vehicles, or the drones, one `.xml` per piece for one zip. Separate
 * archives: a rigger's eight drones and the van they ride in are two
 * different things to drop on a table, and Udonarium reads a whole zip at
 * once. Empty when the character has none of that kind.
 */
export function buildUdonariumVehicles(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
  kind: "vehicles" | "drones" = "drones",
): { name: string; content: string }[] {
  return buildVehiclePieces(ch, catalog, tr, locale, kind).map((p, i) => ({
    name: i ? `data_${i}.xml` : "data.xml",
    content: p.xml,
  }));
}
