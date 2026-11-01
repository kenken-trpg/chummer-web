import type { Catalog, Character } from "@/lib/types";
import { type Locale, type MsgKey, translate } from "@/lib/i18n";
import { vehicleHandling, vehicleSkills } from "@/lib/vtt-pools";

/** A paste accepts one character object, so every owned vehicle gets its own payload. */
export function buildCocofoliaVehicles(
  ch: Character,
  catalog: Catalog,
  tr: (name: string) => string,
  locale: Locale = "ja",
): { id: string; name: string; kind: "vehicles" | "drones"; payload: string }[] {
  const ui = (key: MsgKey) => translate(locale, key);
  const d = ch.derived;
  const at = (key: string) => d.totals?.[key] || 0;
  const number = (value: unknown) => Math.max(0, Number.parseInt(String(value ?? ""), 10) || 0);
  const rating = (name: string) =>
    Math.max(0, (d.skill_totals?.[name] || 0) + (d.skill_bonus?.[name] || 0));
  const { pilots, gunnery } = vehicleSkills(catalog);

  return (["vehicles", "drones"] as const).flatMap((kind) =>
    (d[kind] || []).map((v) => {
      const pilot = number(v.pilot);
      const sensor = number(v.sensor);
      const body = number(v.body);
      const armor = number(v.armor);
      const handling = vehicleHandling(v.handling);
      const commands: string[] = [];
      const roll = (pool: number, label: string, limit?: number) =>
        commands.push(`${Math.max(0, pool)}B6${limit === undefined ? "" : `@${limit}`} ${label}`);

      // Do not guess a flying drone's Pilot skill from its size category.
      for (const skill of pilots.filter((name) => (d.skill_totals?.[name] || 0) > 0)) {
        for (const [attr, label, offroadLabel] of [
          ["REA", "udo.vehicleTest", "udo.vehicleTestOffroad"],
          ["LOG", "udo.vehicleTestRigged", "udo.vehicleTestRiggedOffroad"],
        ] as const) {
          roll(at(attr) + rating(skill), `${ui(label)} / ${tr(skill)}`, handling.onroad);
          if (handling.offroad !== null)
            roll(at(attr) + rating(skill), `${ui(offroadLabel)} / ${tr(skill)}`, handling.offroad);
        }
      }

      const guns = (d.weapons || []).filter(
        (w) => w.mounted_on === v.id && w.modular_equipped !== false,
      );
      for (const w of guns) {
        const info = [
          w.damage && `DV${w.damage}`,
          w.ap && `AP${w.ap}`,
          w.mode && w.mode !== "0" ? w.mode : "",
        ]
          .filter(Boolean)
          .join(" / ");
        const name = `${tr(w.name)}${info ? ` [${info}]` : ""}`;
        const accuracy = String(w.accuracy || "").trim();
        const limit = /^\d+$/.test(accuracy) ? number(accuracy) : undefined;
        roll(at("AGI") + rating(gunnery), `${ui("udo.gunneryByHand")} / ${name}`, limit);
        roll(at("LOG") + rating(gunnery), `${ui("udo.gunneryRigged")} / ${name}`, limit);
      }

      // Keep each installed autosoft separate: Clearsight must never supply
      // the pool for Maneuvering or a different weapon's Targeting program.
      const autosofts = (d.programs || []).filter(
        (p) => p.parent_id === v.id && p.category === "Autosofts" && p.running !== false,
      );
      for (const p of autosofts)
        roll(
          pilot + number(p.rating),
          `${ui("coco.vehicleAutosoft")} / ${p.label || tr(p.name)}${p.extra ? ` (${tr(p.extra)})` : ""}`,
          sensor,
        );
      roll(body + armor, ui("udo.damageResist"));
      roll(pilot * 2, ui("coco.matrixResist"));

      const physical =
        v.condition_monitor ??
        (kind === "drones" ? (v.category === "Drones: Anthro" ? 8 : 6) : 12) + Math.ceil(body / 2);
      const matrix = 8 + Math.ceil(pilot / 2);
      const name = tr(v.name);
      const params = [
        { label: ui("udo.varBody"), value: String(body) },
        { label: ui("udo.varArmor"), value: String(armor) },
        { label: ui("udo.varHandling"), value: v.handling },
        { label: ui("udo.varPilot"), value: String(pilot) },
        { label: ui("udo.varSensor"), value: String(sensor) },
      ];
      const memo = [
        translate(locale, "udo.vehicleName", {
          name,
          category: tr(v.category),
          speed: v.speed,
          accel: v.accel,
        }),
        ui("coco.vehicleNote"),
        !autosofts.length ? ui("coco.vehicleNoAutosofts") : "",
        ui("coco.memoDice"),
      ]
        .filter(Boolean)
        .join("\n");
      return {
        id: v.id,
        name,
        kind,
        payload: JSON.stringify({
          kind: "character",
          data: {
            name,
            memo,
            initiative: 0,
            commands: commands.join("\n"),
            params,
            status: [
              { label: ui("coco.cmPhysical"), value: physical, max: physical },
              { label: ui("coco.cmMatrix"), value: matrix, max: matrix },
            ],
          },
        }),
      };
    }),
  );
}
