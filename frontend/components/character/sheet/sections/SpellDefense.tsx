import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";
import { attrShort } from "@/lib/ui-strings";
import { SPELL_DEFENSE_ROWS } from "@/lib/vtt-pools";

/** The dice a character rolls against each kind of spell (Chummer's
 *  `SpellDefense*`): the engine's pools, an A.I.'s body already its vehicle
 *  home node's. */
export function SpellDefenseSection(s: SheetData) {
  const { d, t } = s;
  const { ui } = useUiText();
  const pools = d.spell_defense_pools;
  return (
    <Section title="sheet.spellDefense" empty={!pools}>
      {pools ? (
        <div className="sheet-derived-grid">
          {SPELL_DEFENSE_ROWS.map(([key, field]) => (
            <div key={field}>
              <span>{ui(key)}</span>
              <b>{pools[field]}</b>
            </div>
          ))}
          {Object.entries(pools.decrease).map(([attr, pool]) => (
            <div key={attr}>
              <span>{ui("sheet.def.decrease", { attr: attrShort(attr, t) })}</span>
              <b>{pool}</b>
            </div>
          ))}
        </div>
      ) : null}
    </Section>
  );
}
