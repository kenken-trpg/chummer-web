/**
 * The house-rule knobs a Chummer settings file can set that this app does not
 * implement — named in words, and split by whether ignoring one can change a
 * number on the sheet.
 *
 * The backend sends `settings.unsupported` as raw Chummer tag names
 * (`specialkarmacostbasedonshownvalue`), which is the right thing to send and
 * the wrong thing to show: a GM reading it cannot tell the knob that re-prices
 * every quality from the one that sets how many decimals Essence prints with.
 * The wording lives here rather than in Python because it is UI text and has
 * to exist in both locales; the tag list it covers is `settings.xml`'s, which
 * `backend/app/settings_file.py` enumerates.
 *
 * `HARMLESS` is the knobs this app can ignore with nothing to say: Chummer's
 * own display and window settings, and rules for things this app has no
 * concept of (enemies, sustaining penalties at the table). Everything else is
 * reported as "numbers may differ", including knobs whose effect is only to
 * offer something extra — a pick list that is missing an option is a
 * difference the table should hear about. When in doubt a knob belongs in the
 * loud group: a dropped house rule nobody was told about is the failure this
 * whole report exists to prevent.
 */
import type { UiFn } from "@/lib/i18n";
import type { MsgKey } from "@/lib/i18n/messages";

/** Knobs with no bearing on anything this app computes or offers. */
export const HARMLESS: ReadonlySet<string> = new Set([
  // how many decimals Essence and nuyen print with, in Chummer's windows
  "essenceformat",
  "nuyenformat",
  // Chummer's own UI: a backstory generator, a dice roller on a pool, and
  // whether an accessory may be edited into the base weapon's own stats
  "autobackstory",
  "allowskilldicerolling",
  "alloweditpartofbaseweapon",
  // Enemies are an SR4 contact type Chummer kept; this app has no enemies, so
  // neither their price nor their quality-limit interaction can land anywhere
  "enableenemytracking",
  "karmaenemy",
  "enemykarmaqualitylimit",
  // A penalty per sustained spell is rolled at the table, not printed here
  "dicepenaltysustaining",
]);

/** `<tag>` -> message key. A tag with no entry is shown as the tag itself. */
const LABELS: Record<string, MsgKey> = {
  allowbiowaresuites: "settings.knob.allowbiowaresuites",
  alloweditpartofbaseweapon: "settings.knob.alloweditpartofbaseweapon",
  allowskilldicerolling: "settings.knob.allowskilldicerolling",
  allowskillregrouping: "settings.knob.allowskillregrouping",
  armordegredation: "settings.knob.armordegredation",
  autobackstory: "settings.knob.autobackstory",
  boundspiritexpression: "settings.knob.boundspiritexpression",
  chargenkarmatonuyenexpression: "settings.knob.chargenkarmatonuyenexpression",
  contactpointsexpression: "settings.knob.contactpointsexpression",
  cyberlimbattributebonuscapoverride: "settings.knob.cyberlimbattributebonuscapoverride",
  dicepenaltysustaining: "settings.knob.dicepenaltysustaining",
  enableenemytracking: "settings.knob.enableenemytracking",
  enemykarmaqualitylimit: "settings.knob.enemykarmaqualitylimit",
  essenceformat: "settings.knob.essenceformat",
  exceednegativequalitieslimit: "settings.knob.exceednegativequalitieslimit",
  extendanydetectionspell: "settings.knob.extendanydetectionspell",
  karmacomplexformoption: "settings.knob.karmacomplexformoption",
  karmacomplexformskillsoft: "settings.knob.karmacomplexformskillsoft",
  karmacontact: "settings.knob.karmacontact",
  karmaenemy: "settings.knob.karmaenemy",
  karmaimprovecomplexform: "settings.knob.karmaimprovecomplexform",
  karmajoingroup: "settings.knob.karmajoingroup",
  karmaleavegroup: "settings.knob.karmaleavegroup",
  karmamaneuver: "settings.knob.karmamaneuver",
  karmametamagic: "settings.knob.karmametamagic",
  karmanewaiadvancedprogram: "settings.knob.karmanewaiadvancedprogram",
  karmanewaiprogram: "settings.knob.karmanewaiprogram",
  karmaquality: "settings.knob.karmaquality",
  karmaspiritfettering: "settings.knob.karmaspiritfettering",
  knowledgepointsexpression: "settings.knob.knowledgepointsexpression",
  morelethalgameplay: "settings.knob.morelethalgameplay",
  mysadeptsecondmagattribute: "settings.knob.mysadeptsecondmagattribute",
  nuyenformat: "settings.knob.nuyenformat",
  priorityspellsasadeptpowers: "settings.knob.priorityspellsasadeptpowers",
  registeredspriteexpression: "settings.knob.registeredspriteexpression",
  reverseattributepriorityorder: "settings.knob.reverseattributepriorityorder",
  specialkarmacostbasedonshownvalue: "settings.knob.specialkarmacostbasedonshownvalue",
};

/** What to call one knob: its sentence, or the bare tag when it is new to us. */
export function knobLabel(tag: string, ui: UiFn): string {
  const key = LABELS[tag];
  return key ? ui(key) : tag;
}

/**
 * The reported tags, split and labelled. `loud` is what can move a number or
 * hide a choice; `quiet` is the rest. Both keep the order the backend gave,
 * which is the order the tags appear sorted — stable between reads.
 */
export function splitKnobs(tags: readonly string[], ui: UiFn): { loud: string[]; quiet: string[] } {
  const loud: string[] = [];
  const quiet: string[] = [];
  for (const tag of tags) (HARMLESS.has(tag) ? quiet : loud).push(knobLabel(tag, ui));
  return { loud, quiet };
}
