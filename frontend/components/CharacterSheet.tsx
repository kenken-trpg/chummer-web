import type { ReactNode } from "react";
import type { Catalog, Character, SpecialArmor } from "@/lib/types";

const ATTRS = ["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA", "EDG", "MAG", "RES"] as const;
const ATTR_JA: Record<string, string> = {
  BOD: "BOD",
  AGI: "AGI",
  REA: "REA",
  STR: "STR",
  WIL: "WIL",
  LOG: "LOG",
  INT: "INT",
  CHA: "CHA",
  EDG: "EDG",
  MAG: "MAG",
  RES: "RES",
};

function lifeIncrement(inc?: string) {
  return inc === "day" ? "日" : "ヶ月";
}

function weaponLine(item: {
  type?: string;
  accuracy?: string;
  damage?: string;
  ap?: string;
  mode?: string;
  ammo?: string;
  reach?: string;
  rc?: string;
}) {
  const bits: string[] = [];
  if (item.type) bits.push(item.type === "Melee" ? "近接" : "遠隔");
  if (item.accuracy && item.accuracy !== "0") bits.push(`Acc ${item.accuracy}`);
  if (item.damage) bits.push(item.damage);
  if (item.ap && item.ap !== "-" && item.ap !== "0") bits.push(`AP ${item.ap}`);
  if (item.rc && item.rc !== "0") bits.push(`RC ${item.rc}`);
  if (item.mode && item.mode !== "0") bits.push(item.mode);
  if (item.ammo && item.ammo !== "0") bits.push(item.ammo);
  if (item.reach && item.reach !== "0") bits.push(`Reach ${item.reach}`);
  return bits.join(" / ");
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
  if (toxinContact && toxinContact === pathogenContact) rows.push({ label: "化学防護(接触)", value: `+${toxinContact}` });
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

function formatPoints(value: number) {
  return String(Math.round(value * 100) / 100);
}

function Section({ title, children, empty }: { title: string; children: ReactNode; empty?: boolean }) {
  if (empty) return null;
  return (
    <section className="sheet-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default function CharacterSheet({
  character,
  catalog,
  tr,
}: {
  character: Character;
  catalog: Catalog;
  tr: (name: string) => string;
}) {
  const d = character.derived;
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
  const knowledge = (d.knowledge_skills || []).filter((row) => row.rating > 0 || row.native || (row.skillsoft || 0) > 0);
  const qualities = d.qualities || [];
  const weapons = d.weapons || [];
  const armors = (d.armor_items || []).filter((item) => item.equipped || item.contributes);
  const cyber = (d.cyberware || []).filter((item) => !item.parent_id);
  const bio = (d.bioware || []).filter((item) => !item.parent_id);
  const isDrug = (item: { category?: string }) =>
    item.category === "Drugs" || item.category === "Toxins" || item.category === "Chemicals";
  const gearMisc = (d.gear || []).filter((item) => !item.parent_id && !isDrug(item));
  const drugs = (d.gear || []).filter((item) => !item.parent_id && isDrug(item));
  const drugChildren = (parentId: string) =>
    (d.gear || []).filter((item) => item.parent_id === parentId);
  const specialArmor = specialArmorBits(d.special_armor);

  return (
    <article className="character-sheet">
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
          <div><span>アーマー</span><b>{d.armor}</b></div>
          <div><span>エッセンス</span><b>{d.essence}</b></div>
          <div><span>ニューエン</span><b>{(d.nuyen ?? 0).toLocaleString()}¥</b></div>
          <div><span>カルマ残</span><b>{d.karma?.remaining ?? 0}/{d.karma?.pool ?? 0}</b></div>
        </div>
      </header>

      <Section title="コア">
        <div className="sheet-core">
          <div className="sheet-attrs">
            {ATTRS.map((key) => {
              if ((key === "MAG" && !enabled.has("MAG")) || (key === "RES" && !enabled.has("RES"))) return null;
              const ware = d.ware_attr_bonus?.[key] || 0;
              return (
                <div className="sheet-attr" key={key}>
                  <span>{ATTR_JA[key]}</span>
                  <b>{totals[key] ?? "-"}</b>
                  {ware ? <em>+{ware}</em> : null}
                </div>
              );
            })}
          </div>
          <div className="sheet-derived-grid">
            <div><span>イニシアチブ</span><b>{d.initiative.value}+{d.initiative.dice}d6</b></div>
            <div><span>コンディション</span><b>P{d.condition_monitor.physical} / S{d.condition_monitor.stun}</b></div>
            <div><span>リミット</span><b>{d.limits.physical} / {d.limits.mental} / {d.limits.social}</b></div>
            <div><span>移動</span><b>歩{d.movement.walk} / 走{d.movement.run}</b></div>
            {(d.damage_resistance || 0) > 0 ? <div><span>ダメージ抵抗</span><b>+{d.damage_resistance}</b></div> : null}
            {(d.unarmed_dv || 0) > 0 ? <div><span>非武装DV</span><b>+{d.unarmed_dv}</b></div> : null}
            {(d.unarmed_reach || 0) > 0 ? <div><span>非武装リーチ</span><b>+{d.unarmed_reach}</b></div> : null}
            {d.lifestyle ? (
              <div>
                <span>ライフスタイル</span>
                <b>
                  {tr(d.lifestyle.name)} {d.lifestyle.months}{lifeIncrement(d.lifestyle.increment)}
                  {d.lifestyle.lp_max ? `（LP ${d.lifestyle.lp_used || 0}/${d.lifestyle.lp_max}）` : ""}
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
              <div key={row.label}><span>{row.label}</span><b>{row.value}</b></div>
            ))}
            {(d.limit_modifiers || []).map((mod, idx) => (
              <div key={`${mod.limit}-${idx}`}>
                <span>条件リミット</span>
                <b>
                  {mod.limit} {mod.value > 0 ? `+${mod.value}` : mod.value}
                  {mod.condition_label || mod.condition ? `（${mod.condition_label || mod.condition}）` : ""}
                </b>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title="スキル" empty={!activeSkills.length && !groups.length && !exotic.length}>
        {groups.length ? (
          <p className="sheet-note">
            グループ:{" "}
            {groups.map((g) => `${tr(g.name)} ${g.rating}${g.bonus ? ` (+${g.bonus})` : ""}`).join(" ・ ")}
          </p>
        ) : null}
        <table className="sheet-table">
          <thead>
            <tr>
              <th>スキル</th>
              <th>属性</th>
              <th>R</th>
              <th>プール</th>
              <th>専門化</th>
            </tr>
          </thead>
          <tbody>
            {activeSkills.map((row) => (
              <tr key={row.name}>
                <td className="left">{tr(row.name)}{row.soft ? " *" : ""}</td>
                <td>{row.attribute}</td>
                <td>{row.rating}</td>
                <td><b>{row.pool}</b></td>
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
                  <td><b>{row.rating + attr}</b></td>
                  <td className="left">{row.extra ? tr(row.extra) : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {activeSkills.some((row) => row.soft) ? <p className="sheet-note">* スキルソフト</p> : null}
      </Section>

      <Section title="知識スキル" empty={!knowledge.length}>
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
                  <td className="left">{tr(row.name)}{row.native ? "（母語）" : ""}{(row.skillsoft || 0) > row.rating ? " *" : ""}</td>
                  <td>{row.category}</td>
                  <td>{rating}</td>
                  <td><b>{rating + attr}</b></td>
                  <td className="left">{row.spec ? tr(row.spec) : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Section>

      <Section title="クオリティ" empty={!qualities.length}>
        <ul className="sheet-list">
          {qualities.map((q) => (
            <li key={q.id}>
              <b>{tr(q.name)}</b>
              {q.extra ? `（${tr(q.extra)}）` : ""}
              <span className="sheet-dim"> {q.category === "Negative" ? "不利" : "有利"} {q.karma > 0 ? `+${q.karma}` : q.karma}K</span>
            </li>
          ))}
        </ul>
      </Section>

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
                  {(item.mods || []).length
                    ? ` ・ ${(item.mods || []).map((m) => tr(m.name)).join("、")}`
                    : ""}
                </li>
              ))}
              {!armors.length && d.worn_armor ? <li><b>{tr(d.worn_armor)}</b></li> : null}
            </ul>
          </div>
        ) : null}
        {weapons.length ? (
          <div className="sheet-block">
            <h4>武器</h4>
            <ul className="sheet-list">
              {weapons.map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.qty > 1 ? ` ×${item.qty}` : ""}
                  {" ・ "}
                  {weaponLine(item)}
                  {(item.focus_dice || 0) > 0 ? ` ・ Focus +${item.focus_dice}d` : ""}
                  {(item.accessories || []).length
                    ? ` ・ ${(item.accessories || []).map((a) => tr(a.name)).join("、")}`
                    : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section title="ウェア" empty={!cyber.length && !bio.length}>
        {cyber.length ? (
          <div className="sheet-block">
            <h4>サイバーウェア（ESS −{d.essence_lost_cyber ?? 0}）</h4>
            <ul className="sheet-list">
              {cyber.map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.rating > 1 ? ` R${item.rating}` : ""}
                  {item.grade && item.grade !== "Standard" ? ` / ${item.grade}` : ""}
                  {item.side ? ` / ${item.side}` : ""}
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

      <Section title="マトリクス" empty={!d.commlink && !d.cyberdeck && !d.rcc && !d.living_persona && !(d.drones || []).length}>
        <ul className="sheet-list">
          {d.commlink ? (
            <li>
              <b>通信機 {tr(d.commlink.name)}</b>
              {" ・ "}DR {d.commlink.device_rating} / DP {d.commlink.dataprocessing} / FW {d.commlink.firewall}
            </li>
          ) : null}
          {d.cyberdeck ? (
            <li>
              <b>デッキ {tr(d.cyberdeck.name)}</b>
              {" ・ "}DR {d.cyberdeck.device_rating} / {d.cyberdeck.attack}/{d.cyberdeck.sleaze}/{d.cyberdeck.dataprocessing}/{d.cyberdeck.firewall}
              {d.cyberdeck.program_max != null ? ` ・ プログラム ${d.cyberdeck.program_used ?? 0}/${d.cyberdeck.program_max}` : ""}
            </li>
          ) : null}
          {d.rcc ? (
            <li>
              <b>RCC {tr(d.rcc.name)}</b>
              {" ・ "}DR {d.rcc.device_rating} / DP {d.rcc.dataprocessing} / FW {d.rcc.firewall}
            </li>
          ) : null}
          {d.living_persona ? (
            <li>
              <b>リビングペルソナ</b>
              {" ・ "}DR {d.living_persona.device_rating} / {d.living_persona.attack}/{d.living_persona.sleaze}/{d.living_persona.dataprocessing}/{d.living_persona.firewall}
              {(d.living_persona.matrix_initiative_dice || 0) > 0
                ? ` ・ マトリクスInit +${d.living_persona.matrix_initiative_dice}d6`
                : ""}
            </li>
          ) : null}
          {(d.drones || []).map((drone) => (
            <li key={drone.id}>
              <b>ドローン {tr(drone.name)}</b>
              {" ・ "}H{drone.handling} Sp{drone.speed} Ac{drone.accel} B{drone.body} A{drone.armor} P{drone.pilot} Se{drone.sensor}
            </li>
          ))}
        </ul>
      </Section>

      <Section
        title="魔法"
        empty={
          !enabled.has("adept")
          && !enabled.has("spells")
          && !enabled.has("spirits")
          && !enabled.has("foci")
          && !enabled.has("initiation")
        }
      >
        {enabled.has("adept") && (d.adept_powers || []).length ? (
          <div className="sheet-block">
            <h4>アデプトパワー（{formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}）</h4>
            <ul className="sheet-list">
              {(d.adept_powers || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.rating > 1 ? ` R${item.total_rating ?? item.rating}` : ""}
                  {item.extra ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("spells") && (d.spells || []).length ? (
          <div className="sheet-block">
            <h4>
              術式
              {d.drain_resist ? ` ・ ドレイン抵抗 ${d.drain_resist.pool}（${d.drain_resist.attrs}）` : ""}
            </h4>
            <ul className="sheet-list">
              {(d.spells || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {" ・ "}
                  {[item.category, item.type, item.range, item.duration, `DV ${item.dv}`].filter(Boolean).join(" / ")}
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
                  {item.extra ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {enabled.has("initiation") && (d.initiation?.grade || 0) > 0 ? (
          <div className="sheet-block">
            <h4>イニシエーション 等級 {d.initiation?.grade}</h4>
            <ul className="sheet-list">
              {(d.initiation?.choices || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  <span className="sheet-dim"> {item.kind === "art" ? "術" : "メタマジック"} G{item.grade}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section
        title="共鳴"
        empty={!enabled.has("complexforms") && !enabled.has("sprites") && !enabled.has("submersion")}
      >
        {enabled.has("complexforms") && (d.complex_forms || []).length ? (
          <div className="sheet-block">
            <h4>
              複合体
              {d.fade_resist ? ` ・ フェード抵抗 ${d.fade_resist.pool}（${d.fade_resist.attrs}）` : ""}
            </h4>
            <ul className="sheet-list">
              {(d.complex_forms || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.label || item.name)}</b>
                  {" ・ "}L{item.level} / FV {item.fv}
                  {item.fade != null ? ` ・ フェード ${item.fade}${item.fade_code || ""}` : ""}
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
            <ul className="sheet-list">
              {(d.submersion?.echoes || []).map((item) => (
                <li key={item.id}>
                  <b>{tr(item.name)}</b>
                  {item.extra ? `（${tr(item.extra)}）` : ""}
                  <span className="sheet-dim"> G{item.grade}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section title="武道" empty={!(d.martial_arts || []).length}>
        <ul className="sheet-list">
          {(d.martial_arts || []).map((art) => (
            <li key={art.id}>
              <b>{tr(art.name)}</b>
              {(art.techniques || []).length
                ? ` ・ ${art.techniques.map((t) => tr(t.name)).join("、")}`
                : ""}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="コネクト" empty={!(d.contacts || []).length}>
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
                <td className="left">{c.name}</td>
                <td className="left">{c.role || ""}</td>
                <td>{c.connection}</td>
                <td>{c.loyalty}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="車両" empty={!(d.vehicles || []).length}>
        <ul className="sheet-list">
          {(d.vehicles || []).map((v) => (
            <li key={v.id}>
              <b>{tr(v.name)}</b>
              {" ・ "}H{v.handling} Sp{v.speed} Ac{v.accel} B{v.body} A{v.armor} P{v.pilot} Se{v.sensor}
              {v.seats ? ` ・ 座席 ${v.seats}` : ""}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="ドラッグ／毒物" empty={!drugs.length}>
        <ul className="sheet-list sheet-list-compact">
          {drugs.map((item) => {
            const grades = drugChildren(item.id);
            return (
              <li key={item.id}>
                {tr(item.name)}
                {(item.qty || 1) > 1 ? ` ×${item.qty}` : ""}
                {grades.length
                  ? `（${grades.map((g) => tr(g.name)).join("、")}）`
                  : ""}
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

      <footer className="sheet-footer">
        Chummer Web ・ 非公式 Shadowrun 5e ・ 卓用表示／印刷
      </footer>
    </article>
  );
}
