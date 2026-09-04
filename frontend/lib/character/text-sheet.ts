import type { SheetData } from "@/lib/character/sheet-data";
import { attrShort } from "@/lib/ui-strings";
import { spellDescriptors, spellDuration, spellRange, spellType } from "@/lib/spell-terms";
import { cfDuration, cfTarget, lifeIncrement, vehicleCM } from "@/lib/character/format";
import type { MsgKey } from "@/lib/i18n";
import { ATTRS } from "@/lib/character/constants";

// The text sheet reads the same bag `buildSheetData()` produces for the
// visual sheet — a subset of it.
export type TextArgs = Pick<
  SheetData,
  | "character"
  | "d"
  | "tr"
  | "t"
  | "ui"
  | "totals"
  | "enabled"
  | "activeSkills"
  | "groups"
  | "exotic"
  | "knowledge"
  | "qualities"
  | "weapons"
  | "armors"
  | "cyber"
  | "bio"
  | "gearMisc"
  | "drugs"
  | "sins"
>;

/** Plain-text "Text-Only" sheet — copy/paste into a VTT or chat. */
export function textSheet(x: TextArgs): string {
  const { character: ch, d, tr, t, ui, totals, enabled } = x;
  const L: string[] = [];
  const line = (s = "") => L.push(s);
  const names = (arr: { name: string }[]) => arr.map((a) => tr(a.name)).join(ui("common.listSep"));
  const head = (key: MsgKey) => line(`=== ${ui(key)} ===`);

  line(ch.name || ui("sheet.unnamed"));
  line(
    `${tr(ch.metatype)}${ch.metavariant ? " / " + tr(ch.metavariant) : ""} ・ ${ch.talent || "Mundane"}` +
      `${d.tradition ? " ・ " + tr(d.tradition.name) : ""}${d.stream ? " ・ " + tr(d.stream.name) : ""}` +
      `${d.mentor ? ui("sheet.mentor", { name: tr(d.mentor.name) }) : ""}`,
  );
  line();

  head("common.attribute");
  line(
    ATTRS.filter(
      (k) => !((k === "MAG" && !enabled.has("MAG")) || (k === "RES" && !enabled.has("RES"))),
    )
      .map((k) => `${attrShort(k, t)} ${totals[k] ?? "-"}`)
      .join("  "),
  );
  line(
    `${ui("common.initiative")} ${d.initiative.value}+${d.initiative.dice}d6  ` +
      `${ui("txt.limits", {
        physical: d.limits.physical,
        mental: d.limits.mental,
        social: d.limits.social,
      })}  ` +
      ui("txt.cm", {
        physical: d.condition_monitor.physical,
        stun: d.condition_monitor.stun,
      }),
  );
  line(
    `${ui("common.armor")} ${d.armor}  ${ui("common.essence")} ${d.essence}  ` +
      ui("txt.movement", { walk: d.movement.walk, run: d.movement.run }),
  );
  line();

  if (x.activeSkills.length || x.groups.length || x.exotic.length) {
    head("sheet.skills");
    x.activeSkills.forEach((s) =>
      line(
        `  ${tr(s.name)}${s.spec ? "（" + tr(s.spec) + "）" : ""} ${s.rating} [${attrShort(s.attribute, t)} ${ui("txt.pool")} ${s.pool}]`,
      ),
    );
    x.exotic.forEach((r) =>
      line(
        `  ${tr(r.label || r.skill_name)}${r.extra ? "（" + tr(r.extra) + "）" : ""} ${r.rating}`,
      ),
    );
    if (x.groups.length)
      line(
        `  ${ui("sheet.groups", {
          list: x.groups
            .map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? `(+${g.bonus})` : ""}`)
            .join(" / "),
        })}`,
      );
    line();
  }

  if (x.knowledge.length) {
    head("sheet.knowledge");
    x.knowledge.forEach((k) =>
      line(
        `  ${tr(k.name)}${k.native ? ui("sheet.native") : ""} ${Math.max(k.rating || 0, k.skillsoft || 0)}${k.spec ? "（" + tr(k.spec) + "）" : ""}`,
      ),
    );
    line();
  }

  if (x.qualities.length) {
    head("sheet.qualities");
    x.qualities.forEach((q) => line(`  ${tr(q.name)}${q.extra ? "：" + tr(q.extra) : ""}`));
    line();
  }

  if (x.weapons.length) {
    head("sheet.weapons");
    x.weapons.forEach((w) =>
      line(
        `  ${tr(w.name)}  DV ${w.damage || "-"} / AP ${w.ap || "-"} / ACC ${w.accuracy || "-"}` +
          `${w.mode ? ` / ${w.mode}` : ""}` +
          `${(w.type || "") !== "Melee" && w.rc_total != null ? ui("txt.rcTotal", { rc: w.rc_total }) : w.rc ? ` / RC ${w.rc}` : ""}` +
          `${(w.accessories || []).length ? `  +${names(w.accessories || [])}` : ""}`,
      ),
    );
    line();
  }

  if (x.armors.length || d.worn_armor) {
    head("gear.kind.armor");
    x.armors.forEach((a) =>
      line(
        `  ${tr(a.name)}  ${a.armor ?? ""}${(a.mods || []).length ? `  +${names(a.mods || [])}` : ""}`,
      ),
    );
    if (!x.armors.length && d.worn_armor) line(`  ${tr(d.worn_armor)}`);
    line();
  }

  if (x.cyber.length || x.bio.length) {
    head("sheet.ware");
    x.cyber.forEach((i) =>
      line(
        `  [${ui("txt.cyber")}] ${tr(i.name)}${i.rating > 1 ? ` R${i.rating}` : ""}` +
          ui("txt.ess", { essence: i.essence }),
      ),
    );
    x.bio.forEach((i) =>
      line(
        `  [${ui("txt.bio")}] ${tr(i.name)}${i.rating > 1 ? ` R${i.rating}` : ""}` +
          ui("txt.ess", { essence: i.essence }),
      ),
    );
    line();
  }

  if (enabled.has("spells") && (d.spells || []).length) {
    head("sheet.spells");
    (d.spells || []).forEach((s) =>
      line(
        `  ${tr(s.name)}  ${tr(s.category || "")} / ${spellType(s.type, ui)} / ${spellRange(s.range, ui)} / ${spellDuration(s.duration, ui)} / DV ${s.dv}` +
          `${s.descriptor ? `（${spellDescriptors(s.descriptor, ui)}）` : ""}`,
      ),
    );
    line();
  }

  if (enabled.has("complexforms") && (d.complex_forms || []).length) {
    head("sheet.complexForms");
    (d.complex_forms || []).forEach((c) =>
      line(
        `  ${tr(c.label || c.name)}  ${cfTarget(c.target, ui)} / ${cfDuration(c.duration, ui)} / L${c.level} / FV ${c.fv}`,
      ),
    );
    line();
  }

  const vehAll = [...(d.vehicles || []), ...(d.drones || [])];
  if (vehAll.length) {
    head("sheet.vehicles");
    vehAll.forEach((v) =>
      line(
        `  ${tr(v.name)}  ` +
          ui("txt.vehicle", {
            handling: v.handling ?? "-",
            speed: v.speed ?? "-",
            accel: v.accel ?? "-",
            body: v.body ?? "-",
            armor: v.armor ?? "-",
            pilot: v.pilot ?? "-",
            sensor: v.sensor ?? "-",
            cm: vehicleCM(v.body),
          }) +
          `${
            (v.mods || []).filter((m) => !m.parent_id).length
              ? ui("txt.vehicleMods", {
                  list: names((v.mods || []).filter((m) => !m.parent_id)),
                })
              : ""
          }`,
      ),
    );
    line();
  }

  if (x.sins.length) {
    head("sheet.sin");
    x.sins.forEach((s) => {
      const lic = (d.gear || []).filter((g) => g.parent_id === s.id);
      line(
        `  ${tr(s.name)}${s.rating > 0 ? ` R${s.rating}` : ""}` +
          `${
            lic.length
              ? ui("txt.licenses", {
                  list: lic
                    .map((l) => `${tr(l.name)}${l.rating > 0 ? ` R${l.rating}` : ""}`)
                    .join(ui("common.listSep")),
                })
              : ""
          }`,
      );
    });
    line();
  }

  if ((d.contacts || []).length) {
    head("sheet.contacts");
    (d.contacts || []).forEach((c) =>
      line(
        `  ${c.name || ui("common.unnamed")}${c.role ? ` / ${tr(c.role)}` : ""}  C${c.connection}/L${c.loyalty}`,
      ),
    );
    line();
  }

  const misc = [...x.gearMisc, ...x.drugs];
  if (misc.length) {
    head("gear.kind.misc");
    misc.forEach((g) =>
      line(
        `  ${g.active ? "▶ " : ""}${tr(g.name)}${g.rating > 1 ? ` R${g.rating}` : ""}${(g.qty || 1) > 1 ? ` ×${g.qty}` : ""}${g.drug_effect ? ` — ${g.drug_effect}` : ""}`,
      ),
    );
    line();
  }
  if ((d.active_drugs || []).length) {
    head("txt.drugsActive");
    (d.active_drugs || []).forEach((drug) =>
      line(
        `  ${tr(drug.name)}${drug.effect ? ` — ${drug.effect}` : ""}${drug.duration ? ui("txt.duration", { duration: drug.duration }) : ""}`,
      ),
    );
    line();
  }

  if (d.lifestyle)
    line(
      ui("print.lifestyle", {
        value: `${tr(d.lifestyle.name)} ${d.lifestyle.months}${lifeIncrement(
          d.lifestyle.increment,
          ui,
        )}`,
      }),
    );
  line(
    ui("txt.money", {
      nuyen: (d.nuyen ?? 0).toLocaleString(),
      remaining: d.karma?.remaining ?? 0,
      pool: d.karma?.pool ?? 0,
    }),
  );

  if ((ch.notes || "").trim()) {
    line();
    head("desc.notes");
    (ch.notes || "").split("\n").forEach((n) => line(`  ${n}`));
  }
  return L.join("\n");
}
