import { Fragment, type ReactNode } from "react";
import type { Catalog, Character, SpecialArmor, WeaponRangeBands } from "@/lib/types";
import { attrShort, makeT } from "@/lib/ui-strings";
import { spellDescriptors, spellDuration, spellRange, spellType } from "@/lib/spell-terms";
import {
  cfDuration,
  cfTarget,
  formatPoints,
  leadInt,
  matrixCM,
  vehicleCM,
} from "@/lib/character/format";
import { ATTRS } from "@/lib/character/constants";
import { textSheet } from "@/lib/character/text-sheet";

// Weapon categories in weapons.xml with no direct entry in ranges.xml.
const RANGE_CAT_ALIAS: Record<string, string> = {
  "Heavy Machine Guns": "Medium/Heavy Machinegun",
  "Medium Machine Guns": "Medium/Heavy Machinegun",
};

/** ranges.xml range name for a weapon: explicit <range>, else category. */
function rangeNameFor(w: { range?: string; category?: string }) {
  return (w.range || "").trim() || RANGE_CAT_ALIAS[w.category || ""] || w.category || "";
}

/** Evaluate a ranges.xml band formula ("5", "{STR}*10", "{STR}/2", "-1"). */
function evalRangeBand(formula: string | undefined, str: number): number | null {
  const f = (formula || "").trim();
  if (!f || f === "-1") return null;
  const m = f
    .replace(/\{STR\}/gi, String(str))
    .match(/^(\d+(?:\.\d+)?)(?:\s*([*/])\s*(\d+(?:\.\d+)?))?$/);
  if (!m) return null;
  let v = parseFloat(m[1]);
  if (m[2] === "*") v *= parseFloat(m[3]);
  else if (m[2] === "/") v /= parseFloat(m[3]);
  return Math.floor(v);
}

/** The four "min–max metre" band strings for a resolved range table entry. */
function rangeRow(bands: WeaponRangeBands, str: number): string[] {
  const nums = [bands.short, bands.medium, bands.long, bands.extreme].map((b) =>
    evalRangeBand(b, str),
  );
  const lows = [evalRangeBand(bands.min, str) ?? 0, nums[0], nums[1], nums[2]];
  return nums.map((hi, i) => {
    if (hi == null) return "–";
    const lo = (lows[i] ?? 0) + (i === 0 ? 0 : 1);
    return `${lo}–${hi}`;
  });
}

function lifeIncrement(inc?: string) {
  return inc === "day" ? "日" : "ヶ月";
}

function specialArmorBits(sa?: SpecialArmor | null): { label: string; value: string }[] {
  if (!sa) return [];
  const rows: { label: string; value: string }[] = [];
  if (sa.fire) rows.push({ label: "耐火", value: `+${sa.fire}` });
  if (sa.cold) rows.push({ label: "断熱", value: `+${sa.cold}` });
  if (sa.electricity) rows.push({ label: "絶縁", value: `+${sa.electricity}` });
  if (sa.radiation) rows.push({ label: "放射線", value: `+${sa.radiation}` });
  const toxinContact = sa.toxin_contact || 0;
  const toxinIngest = sa.toxin_ingestion || 0;
  const toxinInhale = sa.toxin_inhalation || 0;
  const toxinInject = sa.toxin_injection || 0;
  const pathogenContact = sa.pathogen_contact || 0;
  const pathogenIngest = sa.pathogen_ingestion || 0;
  const pathogenInhale = sa.pathogen_inhalation || 0;
  const pathogenInject = sa.pathogen_injection || 0;
  if (toxinContact && toxinContact === pathogenContact)
    rows.push({ label: "化学防護(接触)", value: `+${toxinContact}` });
  else {
    if (toxinContact) rows.push({ label: "毒素接触", value: `+${toxinContact}` });
    if (pathogenContact) rows.push({ label: "病原接触", value: `+${pathogenContact}` });
  }
  if (toxinInhale) rows.push({ label: "毒素吸入", value: `+${toxinInhale}` });
  if (pathogenInhale) rows.push({ label: "病原吸入", value: `+${pathogenInhale}` });
  if (toxinIngest) rows.push({ label: "毒素摂取", value: `+${toxinIngest}` });
  if (pathogenIngest) rows.push({ label: "病原摂取", value: `+${pathogenIngest}` });
  if (toxinInject) rows.push({ label: "毒素注射", value: `+${toxinInject}` });
  if (pathogenInject) rows.push({ label: "病原注射", value: `+${pathogenInject}` });
  const immunities = sa.immunities || {};
  const contact = Boolean(immunities.toxin_contact && immunities.pathogen_contact);
  const inhale = Boolean(immunities.toxin_inhalation && immunities.pathogen_inhalation);
  if (contact && inhale) rows.push({ label: "化学密閉", value: "免疫" });
  else {
    if (contact) rows.push({ label: "接触免疫", value: "免疫" });
    if (inhale) rows.push({ label: "吸入免疫", value: "免疫" });
  }
  return rows;
}

function Section({
  title,
  children,
  empty,
}: {
  title: string;
  children: ReactNode;
  empty?: boolean;
}) {
  if (empty) return null;
  return (
    <section className="sheet-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function GradeList({ items, tr }: { items: any[]; tr: (n: string) => string }) {
  const grades = Array.from(new Set(items.map((i) => Number(i.grade) || 0))).sort((a, b) => a - b);
  return (
    <ul className="sheet-list">
      {grades.map((g) => (
        <li key={g}>
          <b>等級 {g}</b>
          <span className="sheet-dim">
            {" "}
            {items
              .filter((i) => (Number(i.grade) || 0) === g)
              .map(
                (i) =>
                  `${tr(i.name)}${i.extra ? `（${tr(i.extra)}）` : ""}${i.kind === "art" ? "〔術〕" : ""}`,
              )
              .join("、")}
          </span>
        </li>
      ))}
    </ul>
  );
}

function VehicleBlock({ v, tr }: { v: any; tr: (n: string) => string }) {
  const mods = (v.mods || []).filter((m: any) => !m.parent_id);
  const mounts = v.weapon_mounts || [];
  const sensors = v.sensors || [];
  const gear = (v.gear || []).filter((g: any) => !g.parent_id);
  const tracks = v.slot_tracks || [];
  return (
    <div className="sheet-block">
      <h4>
        {tr(v.name)}
        {v.seats ? `（座席 ${v.seats}）` : ""}
      </h4>
      <div className="sheet-derived-grid sheet-vehicle-stats">
        <div>
          <span>機動</span>
          <b>{v.handling || "-"}</b>
        </div>
        <div>
          <span>速度</span>
          <b>{v.speed || "-"}</b>
        </div>
        <div>
          <span>加速</span>
          <b>{v.accel || "-"}</b>
        </div>
        <div>
          <span>車体</span>
          <b>{v.body || "-"}</b>
        </div>
        <div>
          <span>装甲</span>
          <b>{v.armor || "-"}</b>
        </div>
        <div>
          <span>パイロット</span>
          <b>{v.pilot || "-"}</b>
        </div>
        <div>
          <span>センサー</span>
          <b>{v.sensor || "-"}</b>
        </div>
        <div>
          <span>物理CM</span>
          <b>{vehicleCM(v.body)}</b>
        </div>
      </div>
      {mods.length ? (
        <p className="sheet-note">
          改造:{" "}
          {mods
            .map((m: any) => `${tr(m.name)}${(m.rating || 0) > 1 ? ` R${m.rating}` : ""}`)
            .join("、")}
        </p>
      ) : null}
      {mounts.length ? (
        <p className="sheet-note">
          ウェポンマウント:{" "}
          {mounts
            .map(
              (m: any) =>
                `${tr(m.label || m.name)}${m.weapon_name ? `＝${tr(m.weapon_name)}` : "（空）"}`,
            )
            .join("、")}
        </p>
      ) : null}
      {sensors.length ? (
        <p className="sheet-note">センサー機器: {sensors.map((s: any) => tr(s.name)).join("、")}</p>
      ) : null}
      {gear.length ? (
        <p className="sheet-note">搭載ギア: {gear.map((g: any) => tr(g.name)).join("、")}</p>
      ) : null}
      {tracks.length ? (
        <p className="sheet-note">
          スロット: {tracks.map((s: any) => `${s.label} ${s.used}/${s.max}`).join(" ・ ")}
        </p>
      ) : null}
    </div>
  );
}

export type SheetLayout = "standard" | "compact" | "text";

export default function CharacterSheet({
  character,
  catalog,
  tr,
  layout = "standard",
}: {
  character: Character;
  catalog: Catalog;
  tr: (name: string) => string;
  layout?: SheetLayout;
}) {
  const d = character.derived;
  const t = makeT(catalog);
  const totals = d.totals || {};
  const enabled = new Set(d.enabled_tabs || []);

  const activeSkills = (catalog.skills.skills || [])
    .filter((s) => s.source === "SR5" && !s.exotic && !s.name.includes("Exotic"))
    .map((s) => {
      const rating = d.skill_totals?.[s.name] || 0;
      const soft = d.skillsoft?.[s.name] || 0;
      const effective = Math.max(rating, soft);
      const attr = totals[s.attribute] || 0;
      const spec = d.skill_specializations?.[s.name];
      return {
        name: s.name,
        attribute: s.attribute,
        rating: effective,
        pool: effective + attr,
        soft: soft > rating ? soft : 0,
        spec,
      };
    })
    .filter((row) => row.rating > 0)
    .sort((a, b) => tr(a.name).localeCompare(tr(b.name), "ja"));

  const groups = (catalog.skills.groups || [])
    .map((g) => ({
      name: g,
      rating: character.skill_groups?.[g] || 0,
      bonus: d.skill_group_bonus?.[g] || 0,
    }))
    .filter((row) => row.rating > 0 || row.bonus > 0);

  const exotic = (d.exotic_skills || []).filter((row) => row.rating > 0);
  const knowledge = (d.knowledge_skills || []).filter(
    (row) => row.rating > 0 || row.native || (row.skillsoft || 0) > 0,
  );
  const qualities = d.qualities || [];
  const weapons = d.weapons || [];
  const armors = (d.armor_items || []).filter((item) => item.equipped || item.contributes);
  const cyber = (d.cyberware || []).filter((item) => !item.parent_id);
  const bio = (d.bioware || []).filter((item) => !item.parent_id);
  const isDrug = (item: { category?: string }) =>
    item.category === "Drugs" || item.category === "Toxins" || item.category === "Chemicals";
  const isSin = (item: { category?: string }) => item.category === "ID/Credsticks";
  const gearMisc = (d.gear || []).filter(
    (item) => !item.parent_id && !isDrug(item) && !isSin(item),
  );
  const drugs = (d.gear || []).filter((item) => !item.parent_id && isDrug(item));
  const sins = (d.gear || []).filter((item) => !item.parent_id && isSin(item));
  const gearChildren = (parentId: string) =>
    (d.gear || []).filter((item) => item.parent_id === parentId);
  const drugChildren = gearChildren;
  const specialArmor = specialArmorBits(d.special_armor);

  if (layout === "text") {
    return (
      <pre className="sheet-text">
        {textSheet({
          character,
          d,
          tr,
          t,
          totals,
          enabled,
          activeSkills,
          groups,
          exotic,
          knowledge,
          qualities,
          weapons,
          armors,
          cyber,
          bio,
          gearMisc,
          drugs,
          sins,
        })}
      </pre>
    );
  }

  return (
    <article
      className={`character-sheet${layout === "compact" ? " character-sheet--compact" : ""}`}
    >
      <header className="sheet-header">
        <div>
          <p className="sheet-kicker">
            Shadowrun 5e キャラクターシート
            {character.career || d.career ? " ・ キャリア" : " ・ 作成"}
          </p>
          <h2 className="sheet-name">{character.name || "無名のランナー"}</h2>
          <p className="sheet-meta">
            {tr(character.metatype)}
            {character.metavariant ? ` / ${tr(character.metavariant)}` : ""}
            {" ・ "}
            {character.talent || "Mundane"}
            {d.tradition ? ` ・ ${tr(d.tradition.name)}` : ""}
            {d.stream ? ` ・ ${tr(d.stream.name)}` : ""}
            {d.mentor ? ` ・ メンター ${tr(d.mentor.name)}` : ""}
          </p>
        </div>
        <div className="sheet-header-stats">
          <div>
            <span>アーマー</span>
            <b>{d.armor}</b>
          </div>
          <div>
            <span>エッセンス</span>
            <b>{d.essence}</b>
          </div>
          <div>
            <span>ニューエン</span>
            <b>{(d.nuyen ?? 0).toLocaleString()}¥</b>
          </div>
          <div>
            <span>カルマ残</span>
            <b>
              {d.karma?.remaining ?? 0}/{d.karma?.pool ?? 0}
            </b>
          </div>
          {character.career || d.career ? (
            <>
              <div>
                <span>SC</span>
                <b>{d.street_cred || 0}</b>
              </div>
              <div>
                <span>悪名</span>
                <b>{d.notoriety || 0}</b>
              </div>
              <div>
                <span>周知度</span>
                <b>{d.public_awareness || 0}</b>
              </div>
            </>
          ) : null}
        </div>
      </header>

      <Section title="コア">
        <div className="sheet-core">
          <div className="sheet-attrs">
            {ATTRS.map((key) => {
              if ((key === "MAG" && !enabled.has("MAG")) || (key === "RES" && !enabled.has("RES")))
                return null;
              const ware = d.ware_attr_bonus?.[key] || 0;
              return (
                <div className="sheet-attr" key={key}>
                  <span>{attrShort(key, t)}</span>
                  <b>{totals[key] ?? "-"}</b>
                  {ware ? <em>+{ware}</em> : null}
                </div>
              );
            })}
          </div>
          <div className="sheet-derived-grid">
            <div>
              <span>イニシアチブ</span>
              <b>
                {d.initiative.value}+{d.initiative.dice}d6
              </b>
            </div>
            <div>
              <span>コンディション</span>
              <b>
                P{d.condition_monitor.physical} / S{d.condition_monitor.stun}
              </b>
            </div>
            <div>
              <span>リミット</span>
              <b>
                {d.limits.physical} / {d.limits.mental} / {d.limits.social}
              </b>
            </div>
            <div>
              <span>移動</span>
              <b>
                歩{d.movement.walk} / 走{d.movement.run}
              </b>
            </div>
            {(d.damage_resistance || 0) > 0 ? (
              <div>
                <span>ダメージ抵抗</span>
                <b>+{d.damage_resistance}</b>
              </div>
            ) : null}
            {(d.unarmed_dv || 0) > 0 ? (
              <div>
                <span>非武装DV</span>
                <b>+{d.unarmed_dv}</b>
              </div>
            ) : null}
            {(d.unarmed_reach || 0) > 0 ? (
              <div>
                <span>非武装リーチ</span>
                <b>+{d.unarmed_reach}</b>
              </div>
            ) : null}
            {(d.unarmed_ap ?? 0) !== 0 ? (
              <div>
                <span>非武装AP</span>
                <b>{(d.unarmed_ap ?? 0) > 0 ? `+${d.unarmed_ap}` : d.unarmed_ap}</b>
              </div>
            ) : null}
            {d.lifestyle ? (
              <div>
                <span>ライフスタイル</span>
                <b>
                  {tr(d.lifestyle.name)} {d.lifestyle.months}
                  {lifeIncrement(d.lifestyle.increment)}
                  {d.lifestyle.lp_max
                    ? `（LP ${d.lifestyle.lp_used || 0}/${d.lifestyle.lp_max}）`
                    : ""}
                </b>
                {(d.lifestyle.qualities || []).length ? (
                  <em>
                    {(d.lifestyle.qualities || [])
                      .map((q) => `${tr(q.name)}${q.extra ? `:${q.extra}` : ""}`)
                      .join("、")}
                  </em>
                ) : null}
              </div>
            ) : null}
            {specialArmor.map((row) => (
              <div key={row.label}>
                <span>{row.label}</span>
                <b>{row.value}</b>
              </div>
            ))}
            {(d.limit_modifiers || []).map((mod, idx) => (
              <div key={`${mod.limit}-${idx}`}>
                <span>条件リミット</span>
                <b>
                  {mod.limit} {mod.value > 0 ? `+${mod.value}` : mod.value}
                  {mod.condition_label || mod.condition
                    ? `（${mod.condition_label || mod.condition}）`
                    : ""}
                </b>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title="技能" empty={!activeSkills.length && !groups.length && !exotic.length}>
        {groups.length ? (
          <p className="sheet-note">
            グループ:{" "}
            {groups
              .map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? ` (+${g.bonus})` : ""}`)
              .join(" ・ ")}
          </p>
        ) : null}
        <table className="sheet-table">
          <thead>
            <tr>
              <th>技能</th>
              <th>能力値</th>
              <th>R</th>
              <th>プール</th>
              <th>専門化</th>
            </tr>
          </thead>
          <tbody>
            {activeSkills.map((row) => (
              <tr key={row.name}>
                <td className="left">
                  {tr(row.name)}
                  {row.soft ? " *" : ""}
                </td>
                <td>{row.attribute}</td>
                <td>{row.rating}</td>
                <td>
                  <b>{row.pool}</b>
                </td>
                <td className="left">{row.spec ? tr(row.spec) : ""}</td>
              </tr>
            ))}
            {exotic.map((row) => {
              const attr = totals[row.attribute] || 0;
              return (
                <tr key={row.id}>
                  <td className="left">{tr(row.label || row.skill_name)}</td>
                  <td>{row.attribute}</td>
                  <td>{row.rating}</td>
                  <td>
                    <b>{row.rating + attr}</b>
                  </td>
                  <td className="left">{row.extra ? tr(row.extra) : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {activeSkills.some((row) => row.soft) ? <p className="sheet-note">* スキルソフト</p> : null}
      </Section>

      <Section title="知識技能" empty={!knowledge.length}>
        <table className="sheet-table">
          <thead>
            <tr>
              <th>知識</th>
              <th>分類</th>
              <th>R</th>
              <th>プール</th>
              <th>専門化</th>
            </tr>
          </thead>
          <tbody>
            {knowledge.map((row) => {
              const attr = totals[row.attribute] || 0;
              const rating = Math.max(row.rating || 0, row.skillsoft || 0);
              return (
                <tr key={`${row.category}-${row.name}`}>
                  <td className="left">
                    {tr(row.name)}
                    {row.native ? "（母語）" : ""}
                    {(row.skillsoft || 0) > row.rating ? " *" : ""}
                  </td>
                  <td>{tr(row.category)}</td>
                  <td>{rating}</td>
                  <td>
                    <b>{rating + attr}</b>
                  </td>
                  <td className="left">{row.spec ? tr(row.spec) : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Section>

      {character.career || d.career ? (
        <Section title="キャリア">
          <div className="sheet-derived-grid">
            <div>
              <span>報酬合計</span>
              <b>
                {d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥
              </b>
            </div>
            <div>
              <span>成長カルマ</span>
              <b>{d.career_advancement_karma || 0}K</b>
            </div>
            <div>
              <span>SC / 悪名 / 周知</span>
              <b>
                {d.street_cred || 0} / {d.notoriety || 0} / {d.public_awareness || 0}
              </b>
            </div>
          </div>
          {(d.reward_log || []).length ? (
            <div className="sheet-block">
              <h4>報酬履歴</h4>
              <ul className="sheet-list">
                {(d.reward_log || []).map((row) => (
                  <li key={row.id}>
                    <b>{row.label}</b>
                    <span className="sheet-dim">
                      {" "}
                      {row.karma}K / {row.nuyen.toLocaleString()}¥
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {(d.karma_spend_breakdown || []).length ? (
            <div className="sheet-block">
              <h4>カルマ消費内訳</h4>
              <ul className="sheet-list">
                {(d.karma_spend_breakdown || []).map((row, idx) => (
                  <li key={`ks-${idx}`}>
                    <b>{row.label}</b>
                    <span className="sheet-dim"> {row.amount}K</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {(d.nuyen_spend_breakdown || []).length ? (
            <div className="sheet-block">
              <h4>買い物内訳</h4>
              <ul className="sheet-list">
                {(d.nuyen_spend_breakdown || []).map((row, idx) => (
                  <li key={`ns-${idx}`}>
                    <b>{row.label}</b>
                    <span className="sheet-dim"> {row.amount.toLocaleString()}¥</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Section>
      ) : null}

      <Section title="資質" empty={!qualities.length}>
        <ul className="sheet-list">
          {qualities.map((q) => (
            <li key={q.id}>
              <b>{tr(q.name)}</b>
              {q.extra ? `（${tr(q.extra)}）` : ""}
              {q.side ? `（${q.side === "Left" ? "左" : q.side === "Right" ? "右" : q.side}）` : ""}
              <span className="sheet-dim">
                {" "}
                {q.category === "Negative" ? "不利な資質" : "有利な資質"}{" "}
                {q.karma > 0 ? `+${q.karma}` : q.karma}K
              </span>
            </li>
          ))}
        </ul>
        {d.metagenic &&
        (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
          <p className="sheet-dim">
            メタジェネティック: 有利 {d.metagenic.positive} ／ 不利 {d.metagenic.negative}
            {d.metagenic.limit > 0 ? ` ／ 上限 ${d.metagenic.limit}` : ""}
          </p>
        ) : null}
      </Section>

      {(d.action_dice_pools || []).length ? (
        <Section title="アクションDP">
          <ul className="sheet-list">
            {(d.action_dice_pools || []).map((row, idx) => (
              <li key={`${row.name}-${idx}`}>
                <b>{row.category ? `${row.category}: ${tr(row.name)}` : tr(row.name)}</b>
                <span className="sheet-dim">
                  {" "}
                  {row.bonus > 0 ? "+" : ""}
                  {row.bonus}
                </span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <Section title="戦闘" empty={!weapons.length && !armors.length && !d.worn_armor}>
        {armors.length || d.worn_armor ? (
          <div className="sheet-block">
            <h4>アーマー</h4>
            <ul className="sheet-list">
              {(armors.length ? armors : []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {" ・ "}
                  {item.armor_value}
                  {item.equipped ? " ・ 装備中" : ""}
                  {item.has_wireless && item.wireless === false ? " ・ WL切" : ""}
                  {(item.mods || []).length
                    ? ` ・ ${(item.mods || []).map((m) => `${tr(m.name)}${m.has_wireless && m.wireless === false ? "(WL切)" : ""}`).join("、")}`
                    : ""}
                </li>
              ))}
              {!armors.length && d.worn_armor ? (
                <li>
                  <b>{tr(d.worn_armor)}</b>
                </li>
              ) : null}
            </ul>
          </div>
        ) : null}
        {weapons.length ? (
          <div className="sheet-block">
            <h4>武器</h4>
            <table className="sheet-table sheet-table--weapon">
              <thead>
                <tr>
                  <th>武器</th>
                  <th>Acc</th>
                  <th>DV</th>
                  <th>AP</th>
                  <th>モード</th>
                  <th>RC</th>
                  <th>弾数</th>
                  <th>リーチ</th>
                  <th>携帯</th>
                </tr>
              </thead>
              <tbody>
                {weapons.map((item) => {
                  const dash = (v?: string) => (v && v !== "0" && v !== "-" ? v : "–");
                  const sub = [
                    (item.accessories || []).map((a) => tr(a.name)).join("、"),
                    (item.focus_dice || 0) > 0 ? `武器フォーカス +${item.focus_dice}d` : "",
                    item.mounted_label ? `搭載: ${tr(item.mounted_label)}` : "",
                  ]
                    .filter(Boolean)
                    .join(" ・ ");
                  return (
                    <Fragment key={item.id}>
                      <tr>
                        <td className="left">
                          {tr(item.name)}
                          {item.qty > 1 ? ` ×${item.qty}` : ""}
                        </td>
                        <td>{dash(item.accuracy)}</td>
                        <td>{dash(item.damage)}</td>
                        <td>{item.ap && item.ap !== "0" ? item.ap : "–"}</td>
                        <td>{dash(item.mode)}</td>
                        <td>{dash(item.rc)}</td>
                        <td>{dash(item.ammo)}</td>
                        <td>{dash(item.reach)}</td>
                        <td>{dash(item.conceal)}</td>
                      </tr>
                      {sub ? (
                        <tr className="sheet-subrow">
                          <td className="left" colSpan={9}>
                            {sub}
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
            {(() => {
              const table = catalog.weapon_ranges || {};
              const str = totals.STR || 0;
              const names: string[] = [];
              for (const w of weapons) {
                if ((w.type || "") === "Melee") continue;
                for (const n of [rangeNameFor(w), (w.alt_range || "").trim()]) {
                  if (n && table[n] && !names.includes(n)) names.push(n);
                }
              }
              if (!names.length) return null;
              const strScaled = names.some((n) => /\{STR\}/i.test(JSON.stringify(table[n])));
              return (
                <table className="sheet-table sheet-table--range">
                  <thead>
                    <tr>
                      <th>レンジ (m){strScaled ? `・筋力 ${str}` : ""}</th>
                      <th>至近 ±0</th>
                      <th>近 −1</th>
                      <th>中 −3</th>
                      <th>遠 −6</th>
                    </tr>
                  </thead>
                  <tbody>
                    {names.map((name) => {
                      const cells = rangeRow(table[name], str);
                      return (
                        <tr key={name}>
                          <td className="left">{tr(name)}</td>
                          {cells.map((c, i) => (
                            <td key={i}>{c}</td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              );
            })()}
            {(() => {
              const rc = d.recoil;
              const ranged = weapons.filter(
                (w) => (w.type || "") !== "Melee" && (w.mode || "").trim(),
              );
              if (!rc || !ranged.length) return null;
              // net dice penalty for firing `rounds` bullets in one phase, after RC
              const pen = (rounds: number, rcTotal: number) => Math.max(0, rounds - 1 - rcTotal);
              const modeCols: [string, number, RegExp][] = [
                ["SA×2", 2, /SA/],
                ["BF", 3, /BF/],
                ["FA(6)", 6, /FA/],
                ["全弾(10)", 10, /FA/],
              ];
              return (
                <>
                  <table className="sheet-table sheet-table--range">
                    <thead>
                      <tr>
                        <th>反動（RC適用後）</th>
                        <th>合計RC</th>
                        {modeCols.map(([label]) => (
                          <th key={label}>{label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {ranged.map((w) => {
                        const rcTotal = w.rc_total ?? 0;
                        return (
                          <tr key={w.id}>
                            <td className="left">{tr(w.name)}</td>
                            <td>{rcTotal}</td>
                            {modeCols.map(([label, rounds, re]) => (
                              <td key={label}>
                                {re.test(w.mode || "")
                                  ? pen(rounds, rcTotal)
                                    ? `−${pen(rounds, rcTotal)}`
                                    : "±0"
                                  : "–"}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <p className="sheet-note">
                    合計RC ＝ 銃のRC ＋ ⌈筋力 {rc.str}／3⌉ ({rc.str_rc}) ＋ 1。
                    反動は戦闘ターン中に累積し、射撃しないアクションでリセット。
                  </p>
                </>
              );
            })()}
          </div>
        ) : null}
      </Section>

      <Section title="ウェア" empty={!cyber.length && !bio.length}>
        {cyber.length ? (
          <div className="sheet-block">
            <h4>サイバーウェア（ESS −{d.essence_lost_cyber ?? 0}）</h4>
            {d.limb_replace ? (
              <p className="sheet-note">
                サイバーリム平均: STR {d.limb_replace.str} / AGI {d.limb_replace.agi}
                （リム {d.limb_replace.count}/{d.limb_replace.parts}・肉 STR{" "}
                {d.limb_replace.meat_str} / AGI {d.limb_replace.meat_agi}）
              </p>
            ) : null}
            <ul className="sheet-list">
              {cyber.map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.rating > 1 ? ` R${item.rating}` : ""}
                  {item.grade && item.grade !== "Standard" ? ` / ${item.grade}` : ""}
                  {item.side ? ` / ${item.side}` : ""}
                  {item.limb_str != null ? (
                    <span className="sheet-dim">
                      {" "}
                      肢 STR {item.limb_str} / AGI {item.limb_agi}
                      {(item.limb_armor ?? 0) > 0 ? ` / 装甲 ${item.limb_armor}` : ""}
                    </span>
                  ) : null}
                  <span className="sheet-dim"> ESS −{item.essence}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {bio.length ? (
          <div className="sheet-block">
            <h4>バイオウェア（ESS −{d.essence_lost_bio ?? 0}）</h4>
            <ul className="sheet-list">
              {bio.map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.rating > 1 ? ` R${item.rating}` : ""}
                  {item.grade && item.grade !== "Standard" ? ` / ${item.grade}` : ""}
                  <span className="sheet-dim"> ESS −{item.essence}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section
        title="マトリクス"
        empty={!d.commlink && !d.cyberdeck && !d.rcc && !d.living_persona}
      >
        {(() => {
          const rows: {
            key: string;
            label: string;
            dr: number;
            a?: number;
            s?: number;
            dp: number;
            fw: number;
            prog?: string;
            init?: string;
            order?: string;
          }[] = [];
          if (d.commlink)
            rows.push({
              key: "cl",
              label: `通信機 ${tr(d.commlink.name)}`,
              dr: d.commlink.device_rating,
              dp: d.commlink.dataprocessing,
              fw: d.commlink.firewall,
            });
          if (d.cyberdeck) {
            const ck = d.cyberdeck;
            rows.push({
              key: "cd",
              label: `デッキ ${tr(ck.name)}`,
              dr: ck.device_rating,
              a: ck.attack,
              s: ck.sleaze,
              dp: ck.dataprocessing,
              fw: ck.firewall,
              prog:
                ck.program_max != null ? `${ck.program_used ?? 0}/${ck.program_max}` : undefined,
              order: ck.can_reorder && ck.array_order ? ck.array_order.join(" ▸ ") : undefined,
            });
          }
          if (d.rcc)
            rows.push({
              key: "rcc",
              label: `RCC ${tr(d.rcc.name)}`,
              dr: d.rcc.device_rating,
              dp: d.rcc.dataprocessing,
              fw: d.rcc.firewall,
            });
          if (d.living_persona) {
            const lp = d.living_persona;
            rows.push({
              key: "lp",
              label: "リビングペルソナ",
              dr: lp.device_rating,
              a: lp.attack,
              s: lp.sleaze,
              dp: lp.dataprocessing,
              fw: lp.firewall,
              init:
                (lp.matrix_initiative_dice || 0) > 0
                  ? `+${lp.matrix_initiative_dice}d6`
                  : undefined,
            });
          }
          return (
            <>
              <table className="sheet-table sheet-table--matrix">
                <thead>
                  <tr>
                    <th>機器</th>
                    <th>DR</th>
                    <th>A</th>
                    <th>S</th>
                    <th>DP</th>
                    <th>FW</th>
                    <th>Prog</th>
                    <th>M.CM</th>
                    <th>M.Init</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.key}>
                      <td className="left">{r.label}</td>
                      <td>{r.dr}</td>
                      <td>{r.a ?? "–"}</td>
                      <td>{r.s ?? "–"}</td>
                      <td>{r.dp}</td>
                      <td>{r.fw}</td>
                      <td>{r.prog ?? "–"}</td>
                      <td>{matrixCM(r.dr)}</td>
                      <td>{r.init ?? "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {rows.some((r) => r.order) ? (
                <p className="sheet-note">
                  {rows
                    .filter((r) => r.order)
                    .map((r) => `${r.label}: ${r.order}`)
                    .join(" ／ ")}
                </p>
              ) : null}
            </>
          );
        })()}
      </Section>

      <Section
        title="魔法"
        empty={
          !enabled.has("adept") &&
          !enabled.has("spells") &&
          !enabled.has("spirits") &&
          !enabled.has("foci") &&
          !enabled.has("initiation")
        }
      >
        {enabled.has("adept") && (d.adept_powers || []).length ? (
          <div className="sheet-block">
            <h4>
              アデプトパワー（{formatPoints(d.power_points?.used || 0)}/
              {formatPoints(d.power_points?.max || 0)}）
            </h4>
            <ul className="sheet-list">
              {(d.adept_powers || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.rating > 1 ? ` R${item.total_rating ?? item.rating}` : ""}
                  {item.extra
                    ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）`
                    : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("spells") && (d.spells || []).length ? (
          <div className="sheet-block">
            <h4>
              術式
              {d.drain_resist
                ? ` ・ ドレイン抵抗 ${d.drain_resist.pool}（${d.drain_resist.attrs}）`
                : ""}
            </h4>
            <ul className="sheet-list">
              {(d.spells || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.kind && item.kind !== "spell"
                    ? `〔${item.kind === "ritual" ? "儀式" : "付与"}〕`
                    : ""}
                  {" ・ "}
                  {[
                    tr(item.category || ""),
                    spellType(item.type),
                    spellRange(item.range),
                    spellDuration(item.duration),
                    item.damage ? `ダメージ ${item.damage}` : "",
                    `ドレイン ${item.dv}`,
                  ]
                    .filter(Boolean)
                    .join(" / ")}
                  {item.descriptor ? `（${spellDescriptors(item.descriptor)}）` : ""}
                  {item.page ? (
                    <span className="sheet-dim">
                      {" "}
                      {item.source || ""} p.{item.page}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("spirits") && (d.spirits || []).length ? (
          <div className="sheet-block">
            <h4>精霊</h4>
            <ul className="sheet-list">
              {(d.spirits || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {" ・ "}F{item.force}
                  {item.services != null ? ` ・ サービス ${item.services}` : ""}
                  {item.bound ? " ・ 結合" : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("foci") && ((d.foci || []).length || (d.qi_foci || []).length) ? (
          <div className="sheet-block">
            <h4>フォーカス</h4>
            <ul className="sheet-list">
              {(d.foci || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {" ・ "}F{item.force}
                  {item.weapon_name ? `（${tr(item.weapon_name)}）` : ""}
                </li>
              ))}
              {(d.qi_foci || []).map((item) => (
                <li key={item.id}>
                  <b>気フォーカス {tr(item.name)}</b>
                  {" ・ "}R{item.rating}
                  {item.extra
                    ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）`
                    : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("initiation") && (d.initiation?.grade || 0) > 0 ? (
          <div className="sheet-block">
            <h4>イニシエーション 等級 {d.initiation?.grade}</h4>
            {(d.initiation?.choices || []).length ? (
              <GradeList items={d.initiation?.choices || []} tr={tr} />
            ) : (
              <p className="sheet-note">メタマジック未選択</p>
            )}
          </div>
        ) : null}
      </Section>

      <Section
        title="共鳴"
        empty={
          !enabled.has("complexforms") && !enabled.has("sprites") && !enabled.has("submersion")
        }
      >
        {enabled.has("complexforms") && (d.complex_forms || []).length ? (
          <div className="sheet-block">
            <h4>
              複合体
              {d.fade_resist
                ? ` ・ フェード抵抗 ${d.fade_resist.pool}（${d.fade_resist.attrs}）`
                : ""}
            </h4>
            <ul className="sheet-list">
              {(d.complex_forms || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.label || item.name)}</b>
                  {" ・ "}対象 {cfTarget(item.target)} / {cfDuration(item.duration)} / レベル{" "}
                  {item.level} / FV {item.fv}
                  {item.fade != null ? ` ・ フェード ${item.fade}${item.fade_code || ""}` : ""}
                  {item.physical ? "（物理）" : ""}
                  {item.extra ? `（${tr(item.extra)}）` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("sprites") && (d.sprites || []).length ? (
          <div className="sheet-block">
            <h4>スプライト</h4>
            <ul className="sheet-list">
              {(d.sprites || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {" ・ "}L{item.level}
                  {item.services != null ? ` ・ サービス ${item.services}` : ""}
                  {item.registered ? " ・ 登録" : " ・ コンパイル"}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("submersion") && (d.submersion?.grade || 0) > 0 ? (
          <div className="sheet-block">
            <h4>サブマージョン 等級 {d.submersion?.grade}</h4>
            {(d.submersion?.echoes || []).length ? (
              <GradeList items={d.submersion?.echoes || []} tr={tr} />
            ) : (
              <p className="sheet-note">エコー未選択</p>
            )}
          </div>
        ) : null}
      </Section>

      <Section title="武道" empty={!(d.martial_arts || []).length}>
        <ul className="sheet-list">
          {(d.martial_arts || []).map((art) => (
            <li key={art.id}>
              <b>{tr(art.name)}</b>
              {art.free ? " ★" : ""}
              {(art.techniques || []).length
                ? ` ・ ${art.techniques.map((t) => tr(t.name)).join("、")}`
                : " ・ 技未選択"}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="コンタクト" empty={!(d.contacts || []).length}>
        <table className="sheet-table">
          <thead>
            <tr>
              <th>名前</th>
              <th>役割</th>
              <th>C</th>
              <th>L</th>
            </tr>
          </thead>
          <tbody>
            {(d.contacts || []).map((c) => (
              <tr key={c.id}>
                <td className="left">
                  {c.name}
                  {c.free ? " ★" : ""}
                  {c.group ? " (G)" : ""}
                </td>
                <td className="left">{c.role || ""}</td>
                <td>{c.connection}</td>
                <td>{c.loyalty}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section
        title="車両・ドローン"
        empty={!(d.vehicles || []).length && !(d.drones || []).length}
      >
        {(d.vehicles || []).map((v) => (
          <VehicleBlock key={v.id} v={v} tr={tr} />
        ))}
        {(d.drones || []).map((v) => (
          <VehicleBlock key={v.id} v={v} tr={tr} />
        ))}
      </Section>

      <Section title="ドラッグ／毒物" empty={!drugs.length && !(d.active_drugs || []).length}>
        {(d.active_drugs || []).length ? (
          <div className="sheet-block">
            <h4>使用中（能力値・判定に反映済み）</h4>
            <ul className="sheet-list sheet-list-compact">
              {(d.active_drugs || []).map((drug, i) => (
                <li key={`${drug.name}-${i}`}>
                  <b>{tr(drug.name)}</b>
                  {drug.effect ? ` ・ ${drug.effect}` : ""}
                  {drug.duration ? ` ・ 持続 ${drug.duration}` : ""}
                  {drug.vectors?.length ? ` ・ 経路 ${drug.vectors.join("・")}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <ul className="sheet-list sheet-list-compact">
          {drugs.map((item) => {
            const grades = drugChildren(item.id);
            return (
              <li key={item.id}>
                {item.active ? "▶ " : ""}
                {tr(item.name)}
                {(item.qty || 1) > 1 ? ` ×${item.qty}` : ""}
                {grades.length ? `（${grades.map((g) => tr(g.name)).join("、")}）` : ""}
                {item.drug_effect ? (
                  <span className="sheet-dim">{` ・ ${item.drug_effect}`}</span>
                ) : (
                  ""
                )}
              </li>
            );
          })}
        </ul>
      </Section>

      <Section title="SIN／ライセンス" empty={!sins.length}>
        <ul className="sheet-list">
          {sins.map((sin) => {
            const licenses = gearChildren(sin.id);
            return (
              <li key={sin.id}>
                <b>{tr(sin.name)}</b>
                {sin.rating > 0 ? ` R${sin.rating}` : ""}
                {sin.extra ? `（${tr(sin.extra)}）` : ""}
                {licenses.length ? (
                  <span className="sheet-dim">
                    {" ・ "}
                    {licenses
                      .map(
                        (l) =>
                          `${tr(l.name)}${l.rating > 0 ? ` R${l.rating}` : ""}${l.extra ? `:${tr(l.extra)}` : ""}`,
                      )
                      .join("、")}
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      </Section>

      <Section title="その他ギア" empty={!gearMisc.length}>
        <ul className="sheet-list sheet-list-compact">
          {gearMisc.map((item) => (
            <li key={item.id}>
              {tr(item.name)}
              {item.rating > 1 ? ` R${item.rating}` : ""}
              {(item.qty || 1) > 1 ? ` ×${item.qty}` : ""}
            </li>
          ))}
        </ul>
      </Section>

      {(() => {
        const stats: [string, string][] = (
          [
            ["年齢", character.age],
            ["性別", character.sex],
            ["身長", character.height],
            ["体重", character.weight],
            ["目", character.eyes],
            ["髪", character.hair],
            ["肌", character.skin],
            ["コンセプト", character.concept],
          ] as [string, string | undefined][]
        ).filter((r): r is [string, string] => Boolean((r[1] || "").trim()));
        const blocks: [string, string][] = (
          [
            ["容姿", character.appearance],
            ["背景", character.background],
            ["メモ", character.notes],
          ] as [string, string | undefined][]
        ).filter((r): r is [string, string] => Boolean((r[1] || "").trim()));
        if (!stats.length && !blocks.length && !character.portrait) return null;
        return (
          <Section title="記述">
            {character.portrait || stats.length ? (
              <div className="sheet-portrait-row">
                {character.portrait ? (
                  <img className="sheet-portrait" src={character.portrait} alt="ポートレート" />
                ) : null}
                {stats.length ? (
                  <div className="sheet-derived-grid sheet-vehicle-stats">
                    {stats.map(([label, value]) => (
                      <div key={label}>
                        <span>{label}</span>
                        <b>{value}</b>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
            {blocks.map(([label, value]) => (
              <div key={label} className="sheet-block">
                <h4>{label}</h4>
                <p className="sheet-notes">{value}</p>
              </div>
            ))}
          </Section>
        );
      })()}

      <footer className="sheet-footer">Chummer Web ・ 非公式 Shadowrun 5e ・ 卓用表示／印刷</footer>
    </article>
  );
}
