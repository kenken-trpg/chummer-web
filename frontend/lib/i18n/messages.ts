export type Locale = "ja" | "en";

export const LOCALES: readonly Locale[] = ["ja", "en"];

/**
 * `ja` is the reference locale and is always complete — it mirrors the wording
 * the backend engine emits. `en` is intentionally partial; any missing key
 * falls back to the `ja` string, then to the key itself. Add a key to `JA`
 * first; `en` can catch up later. See docs/i18n.md.
 */
const JA = {
  "app.loading": "読み込み中…",
  "app.tagline":
    "非公式 Shadowrun 5e キャラクター作成。Catalyst / Topps 非提携。データは Chummer5a (GPL-3.0)。",

  "locale.label": "言語",
  "locale.ja": "日本語",
  "locale.en": "English",

  "tab.priority": "優先度",
  "tab.meta": "メタ",
  "tab.attrs": "能力値",
  "tab.skills": "技能",
  "tab.qualities": "資質",
  "tab.cyber": "サイバー",
  "tab.bio": "バイオ",
  "tab.gear": "ギア",
  "tab.contacts": "コンタクト",
  "tab.martial": "武道",
  "tab.initiation": "イニシエーション",
  "tab.submersion": "サブマージョン",
  "tab.adept": "アデプト",
  "tab.spells": "術式",
  "tab.spirits": "精霊",
  "tab.foci": "フォーカス",
  "tab.complexforms": "複合体",
  "tab.sprites": "スプライト",
  "tab.check": "チェック",
  "tab.sheet": "シート",

  "check.title": "作成チェック",
  "check.pass": "作成ルール上の問題は見つかりませんでした",
  "check.summary": "エラー {errors}・警告 {warns}・情報 {infos}",
  "check.group.error": "エラー（作成不可）",
  "check.group.warn": "警告",
  "check.group.info": "情報",
  "check.jump": "該当タブへ",

  "share.copy": "共有リンク",
  "share.copied": "コピー ✓",
  "share.title": "共有ビュー（読み取り専用）",
  "share.note": "このキャラクターは URL に埋め込まれています。サーバーには保存されていません。",
  "share.loading": "共有キャラクターを読み込み中…",
  "share.adopt": "自分のロースターに取り込む",
  "share.adopting": "取り込み中…",
  "share.mine": "自分のキャラクターへ",
  "share.layout": "レイアウト",
  "share.print": "印刷 / PDF",
  "share.empty": "共有リンクが指定されていません。",
  "share.long":
    "リンクが長くなりました（{length} 文字）。チャットやメールで途中で切られることがあります。",
  "share.portrait": "ポートレートは共有リンクに含まれません。",
} as const;

export type MsgKey = keyof typeof JA;

const EN: Partial<Record<MsgKey, string>> = {
  "app.loading": "Loading…",
  "app.tagline":
    "Unofficial Shadowrun 5e character creator. Not affiliated with Catalyst / Topps. Data from Chummer5a (GPL-3.0).",

  "locale.label": "Language",

  "tab.priority": "Priority",
  "tab.meta": "Metatype",
  "tab.attrs": "Attributes",
  "tab.skills": "Skills",
  "tab.qualities": "Qualities",
  "tab.cyber": "Cyberware",
  "tab.bio": "Bioware",
  "tab.gear": "Gear",
  "tab.contacts": "Contacts",
  "tab.martial": "Martial Arts",
  "tab.initiation": "Initiation",
  "tab.submersion": "Submersion",
  "tab.adept": "Adept",
  "tab.spells": "Spells",
  "tab.spirits": "Spirits",
  "tab.foci": "Foci",
  "tab.complexforms": "Complex Forms",
  "tab.sprites": "Sprites",
  "tab.check": "Check",
  "tab.sheet": "Sheet",

  "check.title": "Build check",
  "check.pass": "No character-creation rule problems found",
  "check.summary": "{errors} errors · {warns} warnings · {infos} notes",
  "check.group.error": "Errors (build invalid)",
  "check.group.warn": "Warnings",
  "check.group.info": "Notes",
  "check.jump": "Go to tab",

  "share.copy": "Share link",
  "share.copied": "Copied ✓",
  "share.title": "Shared view (read-only)",
  "share.note": "This character is embedded in the URL. Nothing is stored on the server.",
  "share.loading": "Loading the shared character…",
  "share.adopt": "Add to my roster",
  "share.adopting": "Adding…",
  "share.mine": "My characters",
  "share.layout": "Layout",
  "share.print": "Print / PDF",
  "share.empty": "No share payload in this link.",
  "share.long": "The link is long ({length} characters). Chat clients and mail may truncate it.",
  "share.portrait": "Portraits are not included in a share link.",
};

export const MESSAGES: Record<Locale, Partial<Record<MsgKey, string>>> = {
  ja: JA,
  en: EN,
};

/** Substitute `{name}` placeholders; unknown placeholders are left as-is. */
export function formatMessage(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    key in vars ? String(vars[key]) : whole,
  );
}

/** Pure lookup: requested locale → `ja` → the key itself, then interpolate. */
export function translate(
  locale: Locale,
  key: MsgKey,
  vars?: Record<string, string | number>,
): string {
  const template = MESSAGES[locale]?.[key] ?? MESSAGES.ja[key] ?? key;
  return vars ? formatMessage(template, vars) : template;
}
