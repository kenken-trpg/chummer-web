import { useEffect, useEffectEvent, useRef } from "react";
import { api } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";

/** The catalog key of the vendored data: no dataset, no directories. */
const NO_CUSTOM_DATA = "|";

/**
 * Re-read the catalog when the character's custom data changes.
 *
 * The pick lists are built from the catalog, so a merged pack only reaches
 * them if the catalog is the one that pack produces. Keyed on the dataset
 * hash and the enabled directories — the two halves the server keys its
 * merge by — so switching rulesets, or loading the folder for the one
 * already applied, both refetch, and nothing else does.
 *
 * The old catalog stays on screen while the new one is on its way: it is
 * ~3 MB, and blanking every list for the length of that request reads worse
 * than lists that are briefly a merge behind. A failure leaves the old one
 * in place and says so, for the same reason.
 *
 * The catalog itself is owned by {@link useCharacterEditor} — the bootstrap
 * fetches the first one — so this is an effect, not a piece of state.
 */
export function useCatalogReload(opts: {
  ch: Character | null;
  catalog: Catalog | null;
  ui: UiFn;
  setCatalog: (c: Catalog) => void;
  setError: (message: string | null) => void;
}) {
  const { ch, catalog, ui, setCatalog, setError } = opts;
  const dataset = ch?.settings?.dataset ?? "";
  const enabledDirs = (ch?.settings?.customdata ?? []).join("|");
  const catalogKey = `${dataset}|${enabledDirs}`;
  /** The key of the catalog now in `catalog`. The bootstrap fetches the plain
   *  one, which is what no dataset and no directories spell. */
  const loadedKey = useRef(NO_CUSTOM_DATA);
  const catalogLoaded = catalog !== null;
  // `ui` only words the failure; re-running on a locale switch would refetch
  // 3 MB to change a sentence that is not on screen.
  const onReloadError = useEffectEvent((e: unknown) =>
    setError(errorMessage(e, ui, "app.err.catalogReload")),
  );
  const onLoaded = useEffectEvent((next: Catalog) => setCatalog(next));
  useEffect(() => {
    if (!catalogLoaded || loadedKey.current === catalogKey) return;
    let live = true;
    (async () => {
      try {
        const next = await api.catalog({
          dataset,
          customdata: enabledDirs.split("|").filter(Boolean),
        });
        if (!live) return;
        loadedKey.current = catalogKey;
        onLoaded(next);
      } catch (e) {
        if (live) onReloadError(e);
      }
    })();
    return () => {
      live = false;
    };
  }, [catalogKey, catalogLoaded, dataset, enabledDirs]);
}
