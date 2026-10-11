/**
 * Load every UI locale before the suite runs.
 *
 * Only `ja` is bundled; the rest are fetched when something asks to be shown
 * in them (`lib/i18n/messages.ts`). Dozens of tests compare the two locales or
 * call `translate("en", …)` directly, and each one awaiting the fetch would say
 * nothing about the code under test — so the fetch happens once, here, which is
 * what the app does on a locale switch.
 *
 * What this cannot catch is app code that renders in a locale without loading
 * it first. The guard for that is `useLocale`, which never reports a locale
 * whose catalog has not arrived; `lib/i18n/index.test.tsx` pins it, and
 * `messages.test.ts` reaches the pre-load state through `vi.resetModules()`.
 */
import { LOCALES, loadLocale } from "@/lib/i18n/messages";

await Promise.all(LOCALES.map((locale) => loadLocale(locale)));
