/** ルールブックの用語そのもの（技能名・能力値名など） — 日本語。 */
export const JA_RULES = {
  "spec.none": "専門なし",
  "spec.placeholder": "専門化",

  "spec.custom": "自由入力",
  "meta.special": " / 特殊点 {points}",
  "meta.metavariant": "メタバリアント",

  "meta.noVariant": "なし（{name}）",
  "sr.type.mana": "マナ",

  "sr.type.physical": "物理",
  "sr.range.touch": "接触",
  "sr.range.touchArea": "接触(範囲)",
  "sr.range.los": "視認",
  "sr.range.losArea": "視認(範囲)",
  "sr.range.self": "自身",
  "sr.range.selfArea": "自身(範囲)",

  "sr.range.special": "特殊",
  "sr.dur.instant": "即時",
  "sr.dur.permanent": "永続",
  "sr.dur.sustained": "維持",
  "sr.dur.special": "特殊",
  /** Complex forms say 瞬間 where spells say 即時 for the same "Instant"
   *  duration. Kept apart rather than unified under cover of a translation
   *  pass — collapsing them changes what the sheet reads. */
  "sr.dur.instantCf": "瞬間",
  /** Critter powers add a duration spells have no use for: the power is
   *  simply always on (SR5 p.394). */
  "sr.dur.always": "常時",

  /** The action a power takes, in the glossary's words (`Action Type …`):
   *  複雑 / 単純 / 簡易 / なし. `Auto` is the critter table's own — the power
   *  is on without anyone spending an action on it. */
  "sr.action.auto": "自動",
  "sr.action.free": "簡易",
  "sr.action.simple": "単純",
  "sr.action.complex": "複雑",
  "sr.action.special": "特殊",

  "sr.action.none": "なし",
  "sr.desc.area": "効果範囲",
  "sr.desc.extendedArea": "拡大効果範囲",
  "sr.desc.direct": "直接",
  "sr.desc.indirect": "間接",
  "sr.desc.elemental": "元素",
  "sr.desc.mana": "マナ",
  "sr.desc.physical": "物理",
  "sr.desc.realistic": "写実的",
  "sr.desc.active": "能動",
  "sr.desc.passive": "受動",
  "sr.desc.essence": "エッセンス",
  "sr.desc.environmental": "環境",
  "sr.desc.multiSense": "多感覚",
  "sr.desc.singleSense": "単感覚",
  "sr.desc.directional": "指向性",
  "sr.desc.anchored": "固着",
  "sr.desc.blood": "血",
  "sr.desc.mental": "精神",
  "sr.desc.psychic": "精神感応",
  "sr.desc.materialLink": "物質リンク",
  "sr.desc.organicLink": "有機リンク",
  "sr.desc.minion": "従僕",
  "sr.desc.spotter": "観測者",
  "sr.desc.spell": "呪文",
  "sr.desc.contractual": "契約",
  "sr.desc.adept": "アデプト",
  "sr.desc.negative": "負",
  "sr.desc.obvious": "顕在",
  "sr.desc.damaging": "ダメージ有",
  "sr.desc.geomancy": "地霊術",

  // A single spell's kind, where `spell.kind.*` above names a filter tab.
  "sr.desc.object": "物体",
  "sr.kind.spell": "呪文",
  "sr.kind.ritual": "儀式",

  "sr.kind.enchantment": "エンチャント",
  "sr.cf.persona": "ペルソナ",
  "sr.cf.device": "デバイス",
  "sr.cf.host": "ホスト",
  "sr.cf.file": "ファイル",
  "sr.cf.icon": "アイコン",
  "sr.cf.self": "自身",
  "sr.cf.sprite": "スプライト",

  "sr.cf.cyberware": "サイバーウェア",
  "sr.know.academic": "学術",
  "sr.know.interest": "趣味",
  "sr.know.language": "言語",
  "sr.know.professional": "職業",

  // Active-skill category headings, in the rulebook's chapter order.
  "sr.know.street": "街",
  "sr.skillcat.combat": "戦闘技能",
  "sr.skillcat.physical": "肉体技能",
  "sr.skillcat.social": "対人技能",
  "sr.skillcat.magical": "魔法技能",
  "sr.skillcat.pseudomagical": "準魔法技能",
  "sr.skillcat.resonance": "共鳴技能",
  "sr.skillcat.technical": "技術技能",

  "sr.skillcat.vehicle": "操縦技能",
  "sr.spirit.combat": "戦闘",
  "sr.spirit.detection": "探知",
  "sr.spirit.health": "健康",
  "sr.spirit.illusion": "幻影",
  "sr.spirit.manipulation": "操作",

  "sr.spirit.extra": "追加",
  "sr.limb.arm": "腕",
  "sr.limb.leg": "脚",
  "sr.limb.torso": "胴",

  "sr.limb.skull": "頭蓋",
  "sr.r5.powertrain": "パワートレイン",
  "sr.r5.protection": "防護",
  "sr.r5.weapons": "武器",
  "sr.r5.body": "ボディ",
  "sr.r5.electromagnetic": "電磁",

  "sr.r5.cosmetic": "外装",
} as const;
