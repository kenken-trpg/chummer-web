import type { Catalog, Character } from "@/lib/types";
import { attrShort, makeT } from "@/lib/ui-strings";

const ATTR_ORDER = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES"] as const;

/**
 * Build a Cocofolia (ココフォリア) character-piece clipboard payload.
 * `commands` uses BCDice ShadowRun 5th syntax: `NSR5` rolls N d6 and counts hits.
 */
export function buildCocofolia(ch: Character, catalog: Catalog, tr: (n: string) => string): string {
  const d = ch.derived;
  const t = makeT(catalog);
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;

  const skillAttr: Record<string, string> = {};
  for (const s of catalog.skills?.skills || []) skillAttr[s.name] = s.attribute;

  const init = d.initiative || { value: 0, dice: 1 };
  const tm = d.test_mods || {};
  const cmds: string[] = [];

  cmds.push(`${init.dice}D6+${init.value} イニシアチブ`);

  const specs = ch.skill_specializations || {};
  Object.entries(d.skill_totals || {})
    .filter(([, r]) => r > 0)
    .sort((a, b) => tr(a[0]).localeCompare(tr(b[0]), "ja"))
    .forEach(([name, rating]) => {
      const pool = rating + at(skillAttr[name] || "");
      cmds.push(`${pool}SR5 ${tr(name)}`);
      const sp = specs[name];
      if (sp) cmds.push(`${pool + 2}SR5 ${tr(name)}：${tr(sp)}`);
    });

  cmds.push(`${at("REA") + at("INT") + (tm.dodge || 0)}SR5 完全回避`);
  cmds.push(`${at("WIL") + at("CHA") + (tm.composure || 0)}SR5 冷静`);
  cmds.push(`${at("INT") + at("CHA") + (tm.judge_intentions || 0)}SR5 意図看破`);
  cmds.push(`${at("LOG") + at("WIL") + (tm.memory || 0)}SR5 記憶`);
  cmds.push(`${at("STR") + at("BOD")}SR5 運搬`);
  const tabs = d.enabled_tabs || [];
  if (d.drain_resist && tabs.includes("spells"))
    cmds.push(`${d.drain_resist.pool}SR5 ドレイン抵抗（${d.drain_resist.attrs}）`);
  if (d.fade_resist && tabs.includes("complexforms"))
    cmds.push(`${d.fade_resist.pool}SR5 フェード抵抗（${d.fade_resist.attrs}）`);

  const params = ATTR_ORDER.filter((k) => (k !== "MAG" && k !== "RES") || at(k) > 0).map((k) => ({
    label: attrShort(k, t),
    value: String(at(k)),
  }));
  params.push({ label: "物理LIM", value: String(d.limits?.physical ?? 0) });
  params.push({ label: "精神LIM", value: String(d.limits?.mental ?? 0) });
  params.push({ label: "社会LIM", value: String(d.limits?.social ?? 0) });
  params.push({ label: "装甲", value: String(d.armor ?? 0) });
  params.push({ label: "ESS", value: String(d.essence ?? 0) });

  const cm = d.condition_monitor || { physical: 0, stun: 0 };
  const status = [
    { label: "物理CM", value: cm.physical, max: cm.physical },
    { label: "精神CM", value: cm.stun, max: cm.stun },
    { label: "エッジ", value: at("EDG"), max: at("EDG") },
  ];

  const memo = [
    `${tr(ch.metatype)}${ch.metavariant ? " / " + tr(ch.metavariant) : ""} ・ ${ch.talent || "Mundane"}`,
    d.tradition ? `伝統: ${tr(d.tradition.name)}` : "",
    d.mentor ? `メンター: ${tr(d.mentor.name)}` : "",
    `イニシアチブ ${init.value}+${init.dice}d6`,
    `リミット 物${d.limits?.physical} / 精${d.limits?.mental} / 社${d.limits?.social}`,
    `装甲 ${d.armor} ・ エッセンス ${d.essence}`,
  ]
    .filter(Boolean)
    .join("\n");

  return JSON.stringify({
    kind: "character",
    data: {
      name: ch.name || "Runner",
      memo,
      initiative: init.value,
      commands: cmds.join("\n"),
      status,
      params,
    },
  });
}
