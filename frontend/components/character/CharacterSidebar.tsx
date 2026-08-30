"use client";

import { useState } from "react";
import type { Catalog, Character } from "@/lib/types";
import { ATTRS } from "@/lib/character/constants";
import { formatPoints, lifeIncrement, limitModifierLine, specialArmorBits, wareAttrLine } from "@/lib/character/format";
import { attrLabel, makeT } from "@/lib/ui-strings";

export function CharacterSidebar({
  catalog,
  character: ch,
  d,
  tr,
  error,
  patch,
}: {
  catalog: Catalog;
  character: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  error?: string | null;
  patch?: (body: Record<string, unknown>) => void | Promise<void>;
}) {
  const t = makeT(catalog);
  const career = Boolean(ch.career || d.career);
  const rewardLog = d.reward_log || ch.reward_log || [];
  const [rewardLabel, setRewardLabel] = useState("");
  const [rewardKarma, setRewardKarma] = useState(0);
  const [rewardNuyen, setRewardNuyen] = useState(0);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const addReward = () => {
    if (!patch) return;
    const karma = Math.max(0, Number(rewardKarma) || 0);
    const nuyen = Math.max(0, Number(rewardNuyen) || 0);
    if (!karma && !nuyen) return;
    const next = [
      ...rewardLog.map((row) => ({
        id: row.id,
        label: row.label || "報酬",
        karma: Math.max(0, Number(row.karma) || 0),
        nuyen: Math.max(0, Number(row.nuyen) || 0),
      })),
      {
        id: crypto.randomUUID(),
        label: rewardLabel.trim() || "報酬",
        karma,
        nuyen,
      },
    ];
    patch({ reward_log: next });
    setRewardLabel("");
    setRewardKarma(0);
    setRewardNuyen(0);
  };

  const removeReward = (id: string) => {
    if (!patch) return;
    patch({
      reward_log: rewardLog
        .filter((row) => row.id !== id)
        .map((row) => ({
          id: row.id,
          label: row.label || "報酬",
          karma: Math.max(0, Number(row.karma) || 0),
          nuyen: Math.max(0, Number(row.nuyen) || 0),
        })),
    });
  };

  return (
      <aside className="side no-print">
        <h2>{ch.name}</h2>
        <div className="muted">{tr(ch.metatype)}{ch.metavariant ? ` / ${tr(ch.metavariant)}` : ""} ・ {ch.talent}</div>
        <div className="stat">
          <span>モード</span>
          <b>{career ? "キャリア" : "作成"}</b>
        </div>
        <div className="stat">
          <span>作成方式</span>
          <b>
            {(ch.build_method || "Priority") === "Karma"
              ? `Karma ${d.karma.remaining}/${d.karma.pool}`
              : (ch.build_method || "Priority") === "SumToTen"
                ? `Sum to Ten ${d.sum_to_ten?.used ?? 0}/${d.sum_to_ten?.max ?? 10}`
                : "Priority"}
          </b>
        </div>
        {error ? <p className="errors">{error}</p> : null}
        {d.errors.length ? (
          <ul className="errors">{d.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        ) : (
          <p className="ok">{career ? "キャリア進行中" : "作成ルール上は問題なし"}</p>
        )}
        {(d.warnings || []).length ? (
          <ul className="warn">{d.warnings!.map((w) => <li key={w}>{w}</li>)}</ul>
        ) : null}
        <div className="stat"><span>物理/精神/社会リミット</span><b>{d.limits.physical}/{d.limits.mental}/{d.limits.social}</b></div>
        {(d.limit_modifiers || []).map((mod, idx) => (
          <div className="stat" key={`${mod.limit}-${mod.condition || ""}-${idx}`}>
            <span>{limitModifierLine([mod])}</span>
          </div>
        ))}
        <div className="stat"><span>コンディション</span><b>P{d.condition_monitor.physical} / S{d.condition_monitor.stun}</b></div>
        {d.limb_quality ? <div className="stat"><span>リム本数 Quality</span><b>{d.limb_quality.count}本 / {d.limb_quality.pairs}組</b></div> : null}
        <div className="stat"><span>イニシアチブ</span><b>{d.initiative.value}+{d.initiative.dice}d6</b></div>
        <div className="stat"><span>アーマー</span><b>{d.armor}{d.worn_armor ? `（${tr(d.worn_armor)}）` : ""}</b></div>
        {specialArmorBits(d.special_armor).map((row) => (
          <div className="stat" key={row.label}><span>{row.label}</span><b>{row.value}</b></div>
        ))}
        {(d.reach || 0) > 0 ? <div className="stat"><span>リーチ</span><b>+{d.reach}</b></div> : null}
        {(d.lifestyle_cost_mod || 0) !== 0 ? <div className="stat"><span>LSスタイル費用</span><b>{d.lifestyle_cost_mod! > 0 ? "+" : ""}{d.lifestyle_cost_mod}%</b></div> : null}
        {(d.notoriety || 0) !== 0 || career ? (
          <div className="stat">
            <span>悪名</span>
            <b>{(d.notoriety || 0) > 0 ? "+" : ""}{d.notoriety || 0}</b>
          </div>
        ) : null}
        {(d.fame || 0) !== 0 ? <div className="stat"><span>名声</span><b>{d.fame! > 0 ? "+" : ""}{d.fame}</b></div> : null}
        {career || (d.street_cred || 0) > 0 || (d.public_awareness || 0) > 0 ? (
          <>
            <div className="stat"><span>ストリートクレド</span><b>{d.street_cred || 0}</b></div>
            <div className="stat"><span>周知度</span><b>{d.public_awareness || 0}</b></div>
          </>
        ) : (d.public_awareness || 0) !== 0 ? (
          <div className="stat"><span>周知度</span><b>{d.public_awareness! > 0 ? "+" : ""}{d.public_awareness}</b></div>
        ) : null}
        {career && patch ? (
          <div className="career-panel">
            <div className="stat">
              <span>SC 編集</span>
              <input
                type="number"
                min={0}
                value={ch.street_cred || 0}
                onChange={(e) => patch({ street_cred: Math.max(0, Number(e.target.value) || 0) })}
                style={{ width: 64 }}
              />
            </div>
            <div className="stat">
              <span>悪名ボーナス</span>
              <input
                type="number"
                value={ch.notoriety_bonus || 0}
                onChange={(e) => patch({ notoriety_bonus: Number(e.target.value) || 0 })}
                style={{ width: 64 }}
              />
            </div>
            <p className="muted">周知度 = ⌊(SC + max(悪名,0)) / 3⌋ + 品質修正</p>
          </div>
        ) : null}
        {(d.fatigue_resist || 0) !== 0 ? <div className="stat"><span>疲労抵抗</span><b>+{d.fatigue_resist}</b></div> : null}
        {(d.spell_resistance || 0) !== 0 ? <div className="stat"><span>呪文抵抗</span><b>+{d.spell_resistance}</b></div> : null}
        {d.spell_defense && [
          ["直接マナ", d.spell_defense.direct_mana],
          ["探知", d.spell_defense.detection],
          ["精神操作", d.spell_defense.mental_manipulation],
          ["マナ幻影", d.spell_defense.mana_illusion],
          ["物理幻影", d.spell_defense.physical_illusion],
        ].map(([label, value]) =>
          value !== d.spell_defense!.general ? (
            <div className="stat" key={label}>
              <span>{label}</span>
              <b>
                {value > 0 ? "+" : ""}
                {value}
              </b>
            </div>
          ) : null,
        )}
        {(d.action_dice_pools || []).map((row, idx) => (
          <div className="stat" key={`adp-${row.name}-${idx}`}>
            <span>{row.category ? `${row.category}: ${row.name}` : row.name}</span>
            <b>{row.bonus > 0 ? "+" : ""}{row.bonus}</b>
          </div>
        ))}
        {(d.test_mods?.memory || 0) !== 0 ? <div className="stat"><span>記憶</span><b>{d.test_mods!.memory! > 0 ? "+" : ""}{d.test_mods!.memory}</b></div> : null}
        {(d.test_mods?.composure || 0) !== 0 ? <div className="stat"><span>冷静</span><b>{d.test_mods!.composure! > 0 ? "+" : ""}{d.test_mods!.composure}</b></div> : null}
        {(d.test_mods?.judge_intentions || 0) !== 0 ? <div className="stat"><span>意図看破</span><b>{d.test_mods!.judge_intentions! > 0 ? "+" : ""}{d.test_mods!.judge_intentions}</b></div> : null}
        {(d.test_mods?.dodge || 0) !== 0 ? <div className="stat"><span>回避</span><b>{d.test_mods!.dodge! > 0 ? "+" : ""}{d.test_mods!.dodge}</b></div> : null}
        {(d.test_mods?.surprise || 0) !== 0 ? <div className="stat"><span>奇襲</span><b>{d.test_mods!.surprise! > 0 ? "+" : ""}{d.test_mods!.surprise}</b></div> : null}
        <div className="stat"><span>エッセンス</span><b>{d.essence}{(d.essence_lost_cyber || d.essence_lost_bio || d.essence_penalty) ? `（C −${d.essence_lost_cyber ?? 0} / B −${d.essence_lost_bio ?? 0}${(d.essence_penalty || 0) ? ` / その他 −${d.essence_penalty}` : ""}）` : ""}</b></div>
        {(d.cyberware_ess_multiplier || 100) !== 100 ? <div className="stat"><span>サイバーESS</span><b>×{(d.cyberware_ess_multiplier || 100) / 100}</b></div> : null}
        {(d.bioware_ess_multiplier || 100) !== 100 ? <div className="stat"><span>バイオESS</span><b>×{(d.bioware_ess_multiplier || 100) / 100}</b></div> : null}
        {d.ambidextrous ? <div className="stat"><span>利き手</span><b>両利き</b></div> : null}
        {d.erased ? <div className="stat"><span>身元</span><b>Erased（周知度上限1）</b></div> : null}
        {d.excon ? <div className="stat"><span>経歴</span><b>Ex-Con</b></div> : null}
        {d.overclocker ? <div className="stat"><span>オーバークロック</span><b>デッキ +1</b></div> : null}
        {(d.special_modification_limit?.max || 0) > 0 ? (
          <div className="stat">
            <span>特別改造</span>
            <b>{d.special_modification_limit?.used || 0} / {d.special_modification_limit?.max}</b>
          </div>
        ) : null}
        {d.friends_in_high_places ? <div className="stat"><span>コネクト</span><b>FiHP</b></div> : null}
        {d.made_man ? <div className="stat"><span>組織</span><b>Made Man</b></div> : null}
        {(d.trustfund || 0) > 0 ? <div className="stat"><span>信託</span><b>TF{d.trustfund}{d.trustfund_label ? `（${d.trustfund_label}）` : ""}</b></div> : null}
        {(d.dealer_connection_categories || []).length ? <div className="stat"><span>ディーラー</span><b>{(d.dealer_connection_categories || []).join(", ")} −10%</b></div> : null}
        <div className="stat"><span>ニューエン</span><b>{d.nuyen.toLocaleString()}¥</b></div>
        <div className="stat"><span>入手制限</span><b>{d.avail_limit == null ? "制限なし" : d.avail_limit}</b></div>
        <div className="stat"><span>デバイスレーティング</span><b>{d.device_rating_limit ?? 6}</b></div>
        {d.skillwires ? <div className="stat"><span>スキルワイヤ</span><b>R{d.skillwires}</b></div> : null}
        {d.skilljack ? <div className="stat"><span>スキルジャック</span><b>R{d.skilljack}</b></div> : null}
        <div className="stat">
          <span>ウェア強化</span>
          <b>
            {wareAttrLine(d.ware_attr_bonus)
              ? `${wareAttrLine(d.ware_attr_bonus)} / 上限+${d.ware_attr_limit ?? 4}`
              : `+${d.ware_attr_limit ?? 4}`}
          </b>
        </div>
        {d.lifestyle ? <div className="stat"><span>ライフスタイル</span><b>{tr(d.lifestyle.name)} {d.lifestyle.months}{lifeIncrement(d.lifestyle.increment)}</b></div> : null}
        {d.commlink ? <div className="stat"><span>通信機</span><b>{tr(d.commlink.name)} DR{d.commlink.device_rating}</b></div> : null}
        {d.cyberdeck ? <div className="stat"><span>サイバーデッキ</span><b>{tr(d.cyberdeck.name)} DR{d.cyberdeck.device_rating} / {d.cyberdeck.attack}/{d.cyberdeck.sleaze}/{d.cyberdeck.dataprocessing}/{d.cyberdeck.firewall}{d.cyberdeck.program_max ? ` / プログラム ${d.cyberdeck.program_used ?? 0}/${d.cyberdeck.program_max}` : ""}</b></div> : null}
        {d.rcc ? <div className="stat"><span>RCC</span><b>{tr(d.rcc.name)} DR{d.rcc.device_rating} / DP{d.rcc.dataprocessing} FW{d.rcc.firewall}{d.rcc.program_max ? ` / プログラム ${d.rcc.program_used ?? 0}/${d.rcc.program_max}` : ""}</b></div> : null}
        {(d.optics || []).some((item) => !item.parent_id) ? (
          <div className="stat"><span>視覚／聴覚</span><b>{(d.optics || []).filter((item) => !item.parent_id).length}件</b></div>
        ) : null}
        {(d.sensors || []).some((item) => !item.parent_id) ? (
          <div className="stat"><span>センサー</span><b>{(d.sensors || []).filter((item) => !item.parent_id).length}件</b></div>
        ) : null}
        {(d.drones || []).length ? (
          <div className="stat"><span>ドローン</span><b>{(d.drones || []).length}件</b></div>
        ) : null}
        <div className="stat"><span>カルマ</span><b>{d.karma.remaining} / {d.karma.pool}</b></div>
        {career && patch ? (
          <div className="career-panel">
            <div className="stat"><span>報酬合計</span><b>{d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥</b></div>
            {(rewardLog || []).map((row) => (
              <div className="stat" key={row.id}>
                <span className="muted">{row.label || "報酬"} · {row.karma || 0}K / {(row.nuyen || 0).toLocaleString()}¥</span>
                <button type="button" className="btn danger" style={{ padding: "2px 6px", fontSize: "0.75rem" }} onClick={() => row.id && removeReward(row.id)}>削除</button>
              </div>
            ))}
            <label className="muted">
              ラベル
              <input value={rewardLabel} onChange={(e) => setRewardLabel(e.target.value)} placeholder="Run 名など" />
            </label>
            <div className="stat">
              <span>K</span>
              <input type="number" min={0} value={rewardKarma} onChange={(e) => setRewardKarma(Math.max(0, Number(e.target.value) || 0))} style={{ width: 56 }} />
            </div>
            <div className="stat">
              <span>¥</span>
              <input type="number" min={0} step={1000} value={rewardNuyen} onChange={(e) => setRewardNuyen(Math.max(0, Number(e.target.value) || 0))} style={{ width: 96 }} />
            </div>
            <button type="button" className="btn" onClick={addReward}>報酬を追加</button>
            <button type="button" className="btn" onClick={() => setShowBreakdown((v) => !v)}>
              {showBreakdown ? "内訳を隠す" : "成長／買い物の内訳"}
            </button>
            {showBreakdown ? (
              <div className="career-breakdown">
                <p className="muted">カルマ消費</p>
                {(d.karma_spend_breakdown || []).length ? (
                  (d.karma_spend_breakdown || []).map((row, idx) => (
                    <div className="stat" key={`k-${row.label}-${idx}`}>
                      <span>{row.label}</span>
                      <b>{row.amount}K</b>
                    </div>
                  ))
                ) : (
                  <p className="muted">なし</p>
                )}
                <p className="muted">ニューエン消費</p>
                {(d.nuyen_spend_breakdown || []).length ? (
                  (d.nuyen_spend_breakdown || []).map((row, idx) => (
                    <div className="stat" key={`y-${row.label}-${idx}`}>
                      <span>{row.label}</span>
                      <b>{row.amount.toLocaleString()}¥</b>
                    </div>
                  ))
                ) : (
                  <p className="muted">なし</p>
                )}
              </div>
            ) : null}
          </div>
        ) : null}
        {(d.career_advancement_karma || 0) > 0 ? (
          <div className="stat"><span>成長カルマ</span><b>{d.career_advancement_karma}K</b></div>
        ) : null}
        <div className="stat">
          <span>不利カルマ</span>
          <b>
            {d.karma.negative?.used || 0}
            {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
          </b>
        </div>
        <div className="stat"><span>能力値点</span><b>{d.points.attributes.used}/{d.points.attributes.max}</b></div>
        <div className="stat"><span>特殊点</span><b>{d.points.special.used}/{d.points.special.max}</b></div>
        <div className="stat"><span>技能点</span><b>{d.points.skills.used}/{d.points.skills.max}</b></div>
        <div className="stat"><span>知識点</span><b>{d.points.knowledge.used}/{d.points.knowledge.max}</b></div>
        <div className="stat"><span>コネクト</span><b>{d.contact_points?.used || 0}/{d.contact_points?.free || 0}{(d.contact_points?.paid || 0) > 0 ? ` +${d.contact_points?.paid}` : ""}</b></div>
        <div className="stat"><span>武道</span><b>{d.martial_art_points?.styles || 0}/{d.martial_art_points?.style_max || 1}流派 ・ {d.martial_art_points?.techniques || 0}/{d.martial_art_points?.technique_max || 5}技{(d.martial_art_points?.karma || 0) > 0 ? ` / ${d.martial_art_points?.karma}K` : ""}</b></div>
        {d.enabled_tabs.includes("initiation") ? (
          <div className="stat"><span>イニシエーション</span><b>等級 {d.initiation?.grade || 0}{(d.initiation?.karma || 0) > 0 ? ` / ${d.initiation?.karma}K` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("submersion") ? (
          <div className="stat"><span>サブマージョン</span><b>等級 {d.submersion?.grade || 0}{(d.submersion?.karma || 0) > 0 ? ` / ${d.submersion?.karma}K` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("adept") ? (
          <div className="stat"><span>パワー点</span><b>{formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}</b></div>
        ) : null}
        {d.enabled_tabs.includes("spells") ? (
          <div className="stat"><span>術式</span><b>{d.spell_points?.used || 0}/{d.spell_points?.free || 0}{(d.spell_points?.paid || 0) > 0 ? ` +${d.spell_points?.paid}` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("spirits") ? (
          <div className="stat"><span>精霊</span><b>{d.spirits?.length || 0}</b></div>
        ) : null}
        {d.enabled_tabs.includes("foci") ? (
          <div className="stat"><span>フォーカス</span><b>{d.focus_limits?.count || 0}/{d.focus_limits?.count_max || 0}</b></div>
        ) : null}
        {d.enabled_tabs.includes("complexforms") ? (
          <div className="stat"><span>複合体</span><b>{d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}{(d.complex_form_points?.paid || 0) > 0 ? ` +${d.complex_form_points?.paid}` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("sprites") ? (
          <div className="stat"><span>スプライト</span><b>{d.sprites?.length || 0}</b></div>
        ) : null}
        {d.living_persona ? (
          <div className="stat"><span>リビングペルソナ</span><b>DR{d.living_persona.device_rating} / {d.living_persona.attack}/{d.living_persona.sleaze}/{d.living_persona.dataprocessing}/{d.living_persona.firewall}{(d.living_persona.matrix_initiative_dice || 0) > 0 ? ` / マトリクスInit+${d.living_persona.matrix_initiative_dice}d6` : ""}</b></div>
        ) : null}
        {d.tradition ? <div className="stat"><span>伝統</span><b>{tr(d.tradition.name)}</b></div> : null}
        {d.needs_mentor && d.mentor ? <div className="stat"><span>メンター</span><b>{tr(d.mentor.name)}</b></div> : null}
        {(d.damage_resistance || 0) > 0 ? <div className="stat"><span>ダメージ抵抗</span><b>+{d.damage_resistance}</b></div> : null}
        {(d.unarmed_dv || 0) > 0 ? <div className="stat"><span>非武装DV</span><b>+{d.unarmed_dv}</b></div> : null}
        <h3>能力値</h3>
        {ATTRS.map((k) => {
          const hidden = (k === "MAG" && !d.enabled_tabs.includes("MAG")) || (k === "RES" && !d.enabled_tabs.includes("RES"));
          if (hidden) return null;
          return (
            <div className="stat" key={k}>
              <span>{attrLabel(k, t)}</span>
              <b>
                {d.totals[k] ?? "-"}
                {(d.ware_attr_bonus?.[k] || 0) !== 0 ? (
                  <span className="muted"> ウェア+{d.ware_attr_bonus![k]}</span>
                ) : null}
                {d.limb_replace && (k === "STR" || k === "AGI") ? (
                  <span className="muted"> リム平均</span>
                ) : null}
              </b>
            </div>
          );
        })}
        {d.unimplemented_bonuses.length > 0 && (
          <p className="warn">未実装ボーナス {d.unimplemented_bonuses.length} 件（無視して継続）</p>
        )}
      </aside>

  );
}
