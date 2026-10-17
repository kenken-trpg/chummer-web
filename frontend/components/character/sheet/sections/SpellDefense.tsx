import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import type { MsgKey } from "@/lib/i18n";
import { useUiText } from "@/lib/i18n";
import { attrShort } from "@/lib/ui-strings";

type Pools = NonNullable<SheetData["d"]["spell_defense_pools"]>;

/** Chummer's spell defense box, in its order. */
const ROWS: [MsgKey, Exclude<keyof Pools, "decrease">][] = [
  ["sheet.def.indirectDodge", "indirect_dodge"],
  ["sheet.def.indirectSoak", "indirect_soak"],
  ["side.def.directMana", "direct_mana"],
  ["sheet.def.directPhysical", "direct_physical"],
  ["side.def.detection", "detection"],
  ["side.def.manaIllusion", "mana_illusion"],
  ["side.def.physicalIllusion", "physical_illusion"],
  ["side.def.mentalManipulation", "mental_manipulation"],
  ["sheet.def.physicalManipulation", "physical_manipulation"],
];

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
          {ROWS.map(([key, field]) => (
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
