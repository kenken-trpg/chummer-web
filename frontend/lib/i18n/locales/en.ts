/** The English dictionary. Typed `Catalog`, so it cannot fall a key behind
 *  `JA`. Split the same way `ja.ts` is — see the note there. */
import type { Catalog } from "./ja";
import { EN_APP } from "./en/app";
import { EN_CHARGEN } from "./en/chargen";
import { EN_ENGINE } from "./en/engine";
import { EN_GEAR } from "./en/gear";
import { EN_HELP } from "./en/help";
import { EN_MAGIC } from "./en/magic";
import { EN_RULES } from "./en/rules";
import { EN_SHEET } from "./en/sheet";
import { EN_SIDEBAR } from "./en/sidebar";

export const EN: Catalog = {
  ...EN_APP,
  ...EN_ENGINE,
  ...EN_SHEET,
  ...EN_SIDEBAR,
  ...EN_RULES,
  ...EN_CHARGEN,
  ...EN_GEAR,
  ...EN_MAGIC,
  ...EN_HELP,
};
