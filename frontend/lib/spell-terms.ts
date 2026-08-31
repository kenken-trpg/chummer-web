// SR5 spell metadata → Japanese. Fixed vocabularies from the rulebook, so a
// static map is enough (no lang-file round-trip).

const SPELL_TYPE: Record<string, string> = {
  M: "マナ",
  P: "物理",
};

const SPELL_RANGE: Record<string, string> = {
  T: "接触",
  "T (A)": "接触(範囲)",
  LOS: "視認",
  "LOS (A)": "視認(範囲)",
  S: "自身",
  "S (A)": "自身(範囲)",
  Special: "特殊",
};

const SPELL_DURATION: Record<string, string> = {
  I: "即時",
  P: "永続",
  S: "維持",
  Special: "特殊",
};

const SPELL_DESCRIPTOR: Record<string, string> = {
  Area: "効果範囲",
  "Extended Area": "拡大効果範囲",
  Direct: "直接",
  Indirect: "間接",
  Elemental: "元素",
  Mana: "マナ",
  Physical: "物理",
  Realistic: "写実的",
  Active: "能動",
  Passive: "受動",
  Essence: "エッセンス",
  Environmental: "環境",
  "Multi-Sense": "多感覚",
  "Single-Sense": "単感覚",
  Directional: "指向性",
  Anchored: "固着",
  Blood: "血",
  Mental: "精神",
  Psychic: "精神感応",
  "Material Link": "物質リンク",
  "Organic Link": "有機リンク",
  Minion: "従僕",
  Spotter: "観測者",
  Spell: "呪文",
  Contractual: "契約",
  Adept: "アデプト",
  Negative: "負",
  Obvious: "顕在",
  Damaging: "ダメージ有",
  Geomancy: "地霊術",
  Object: "物体",
};

export const spellType = (v?: string | null): string => (v && SPELL_TYPE[v]) || v || "";
export const spellRange = (v?: string | null): string => (v && SPELL_RANGE[v]) || v || "";
export const spellDuration = (v?: string | null): string => (v && SPELL_DURATION[v]) || v || "";

/** "Indirect, Elemental, Area" → "間接・元素・効果範囲" */
export const spellDescriptors = (v?: string | null): string =>
  (v || "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean)
    .map((t) => SPELL_DESCRIPTOR[t] || t)
    .join("・");
