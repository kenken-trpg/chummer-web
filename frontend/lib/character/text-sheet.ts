import type { SheetData } from "@/lib/character/sheet-data";
import { attrShort } from "@/lib/ui-strings";
import { spellDescriptors, spellDuration, spellRange, spellType } from "@/lib/spell-terms";
import { cfDuration, cfTarget, vehicleCM } from "@/lib/character/format";
import { ATTRS } from "@/lib/character/constants";

// The text sheet reads the same bag `buildSheetData()` produces for the
// visual sheet — a subset of it.
export type TextArgs = Pick<
  SheetData,
  | "character"
  | "d"
  | "tr"
  | "t"
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
  const { character: ch, d, tr, t, totals, enabled } = x;
  const L: string[] = [];
  const line = (s = "") => L.push(s);
  const names = (arr: { name: string }[]) => arr.map((a) => tr(a.name)).join("、");

  line(ch.name || "無名のランナー");
  line(
    `${tr(ch.metatype)}${ch.metavariant ? " / " + tr(ch.metavariant) : ""} ・ ${ch.talent || "Mundane"}` +
      `${d.tradition ? " ・ " + tr(d.tradition.name) : ""}${d.stream ? " ・ " + tr(d.stream.name) : ""}` +
      `${d.mentor ? " ・ メンター " + tr(d.mentor.name) : ""}`,
  );
  line();

  line("=== 能力値 ===");
  line(
    ATTRS.filter(
      (k) => !((k === "MAG" && !enabled.has("MAG")) || (k === "RES" && !enabled.has("RES"))),
    )
      .map((k) => `${attrShort(k, t)} ${totals[k] ?? "-"}`)
      .join("  "),
  );
  line(
    `イニシアチブ ${d.initiative.value}+${d.initiative.dice}d6  ` +
      `リミット 物${d.limits.physical}/精${d.limits.mental}/社${d.limits.social}  ` +
      `CM P${d.condition_monitor.physical}/S${d.condition_monitor.stun}`,
  );
  line(
    `アーマー ${d.armor}  エッセンス ${d.essence}  移動 歩${d.movement.walk}/走${d.movement.run}`,
  );
  line();

  if (x.activeSkills.length || x.groups.length || x.exotic.length) {
    line("=== 技能 ===");
    x.activeSkills.forEach((s) =>
      line(
        `  ${tr(s.name)}${s.spec ? "（" + tr(s.spec) + "）" : ""} ${s.rating} [${attrShort(s.attribute, t)} プール ${s.pool}]`,
      ),
    );
    x.exotic.forEach((r) =>
      line(
        `  ${tr(r.label || r.skill_name)}${r.extra ? "（" + tr(r.extra) + "）" : ""} ${r.rating}`,
      ),
    );
    if (x.groups.length)
      line(
        `  グループ: ${x.groups.map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? `(+${g.bonus})` : ""}`).join(" / ")}`,
      );
    line();
  }

  if (x.knowledge.length) {
    line("=== 知識技能 ===");
    x.knowledge.forEach((k) =>
      line(
        `  ${tr(k.name)}${k.native ? "（母語）" : ""} ${Math.max(k.rating || 0, k.skillsoft || 0)}${k.spec ? "（" + tr(k.spec) + "）" : ""}`,
      ),
    );
    line();
  }

  if (x.qualities.length) {
    line("=== 資質 ===");
    x.qualities.forEach((q) => line(`  ${tr(q.name)}${q.extra ? "：" + tr(q.extra) : ""}`));
    line();
  }

  if (x.weapons.length) {
    line("=== 武器 ===");
    x.weapons.forEach((w) =>
      line(
        `  ${tr(w.name)}  DV ${w.damage || "-"} / AP ${w.ap || "-"} / ACC ${w.accuracy || "-"}` +
          `${w.mode ? ` / ${w.mode}` : ""}` +
          `${(w.type || "") !== "Melee" && w.rc_total != null ? ` / 合計RC ${w.rc_total}` : w.rc ? ` / RC ${w.rc}` : ""}` +
          `${(w.accessories || []).length ? `  +${names(w.accessories || [])}` : ""}`,
      ),
    );
    line();
  }

  if (x.armors.length || d.worn_armor) {
    line("=== 防具 ===");
    x.armors.forEach((a) =>
      line(
        `  ${tr(a.name)}  ${a.armor ?? ""}${(a.mods || []).length ? `  +${names(a.mods || [])}` : ""}`,
      ),
    );
    if (!x.armors.length && d.worn_armor) line(`  ${tr(d.worn_armor)}`);
    line();
  }

  if (x.cyber.length || x.bio.length) {
    line("=== ウェア ===");
    x.cyber.forEach((i) =>
      line(`  [サイバー] ${tr(i.name)}${i.rating > 1 ? ` R${i.rating}` : ""}（ESS ${i.essence}）`),
    );
    x.bio.forEach((i) =>
      line(`  [バイオ] ${tr(i.name)}${i.rating > 1 ? ` R${i.rating}` : ""}（ESS ${i.essence}）`),
    );
    line();
  }

  if (enabled.has("spells") && (d.spells || []).length) {
    line("=== 術式 ===");
    (d.spells || []).forEach((s) =>
      line(
        `  ${tr(s.name)}  ${tr(s.category || "")} / ${spellType(s.type)} / ${spellRange(s.range)} / ${spellDuration(s.duration)} / DV ${s.dv}` +
          `${s.descriptor ? `（${spellDescriptors(s.descriptor)}）` : ""}`,
      ),
    );
    line();
  }

  if (enabled.has("complexforms") && (d.complex_forms || []).length) {
    line("=== 複合体 ===");
    (d.complex_forms || []).forEach((c) =>
      line(
        `  ${tr(c.label || c.name)}  ${cfTarget(c.target)} / ${cfDuration(c.duration)} / L${c.level} / FV ${c.fv}`,
      ),
    );
    line();
  }

  const vehAll = [...(d.vehicles || []), ...(d.drones || [])];
  if (vehAll.length) {
    line("=== 車両・ドローン ===");
    vehAll.forEach((v) =>
      line(
        `  ${tr(v.name)}  機動${v.handling} 速${v.speed} 加${v.accel} 車体${v.body} 装甲${v.armor} ` +
          `操縦${v.pilot} センサー${v.sensor} CM${vehicleCM(v.body)}` +
          `${(v.mods || []).filter((m) => !m.parent_id).length ? `  改造: ${names((v.mods || []).filter((m) => !m.parent_id))}` : ""}`,
      ),
    );
    line();
  }

  if (x.sins.length) {
    line("=== SIN／ライセンス ===");
    x.sins.forEach((s) => {
      const lic = (d.gear || []).filter((g) => g.parent_id === s.id);
      line(
        `  ${tr(s.name)}${s.rating > 0 ? ` R${s.rating}` : ""}` +
          `${lic.length ? `  ライセンス: ${lic.map((l) => `${tr(l.name)}${l.rating > 0 ? ` R${l.rating}` : ""}`).join("、")}` : ""}`,
      );
    });
    line();
  }

  if ((d.contacts || []).length) {
    line("=== コンタクト ===");
    (d.contacts || []).forEach((c) =>
      line(
        `  ${c.name || "（無名）"}${c.role ? ` / ${tr(c.role)}` : ""}  C${c.connection}/L${c.loyalty}`,
      ),
    );
    line();
  }

  const misc = [...x.gearMisc, ...x.drugs];
  if (misc.length) {
    line("=== ギア ===");
    misc.forEach((g) =>
      line(
        `  ${g.active ? "▶ " : ""}${tr(g.name)}${g.rating > 1 ? ` R${g.rating}` : ""}${(g.qty || 1) > 1 ? ` ×${g.qty}` : ""}${g.drug_effect ? ` — ${g.drug_effect}` : ""}`,
      ),
    );
    line();
  }
  if ((d.active_drugs || []).length) {
    line("=== 使用中のドラッグ（反映済み） ===");
    (d.active_drugs || []).forEach((drug) =>
      line(
        `  ${tr(drug.name)}${drug.effect ? ` — ${drug.effect}` : ""}${drug.duration ? ` / 持続 ${drug.duration}` : ""}`,
      ),
    );
    line();
  }

  if (d.lifestyle)
    line(
      `ライフスタイル: ${tr(d.lifestyle.name)} ${d.lifestyle.months}${d.lifestyle.increment === "day" ? "日" : "ヶ月"}`,
    );
  line(
    `ニューエン ${(d.nuyen ?? 0).toLocaleString()}¥  カルマ残 ${d.karma?.remaining ?? 0}/${d.karma?.pool ?? 0}`,
  );

  if ((ch.notes || "").trim()) {
    line();
    line("=== メモ ===");
    (ch.notes || "").split("\n").forEach((n) => line(`  ${n}`));
  }
  return L.join("\n");
}
