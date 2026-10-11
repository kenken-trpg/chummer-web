/**
 * Udonarium (ユドナリウム) character export — one piece as a `data.xml`.
 *
 * Pieces go out in a `.zip`: dropping a file on the table reads a bare `.xml`
 * too, but the 「ZIP読込」 file input unzips whatever it is handed, so only a
 * zip goes in both ways — and the zip is what carries the portrait.
 *
 * Unlike the Cocofolia export, which hands the table a finished number for
 * every roll, Udonarium's chat palette has variables: `//敏捷力=5` defines one
 * and `{敏捷力}` reads it back. That is the point of the template this follows
 * — the table can retune a pool mid-session without re-exporting. It only
 * works where a roll decomposes into named parts, so this export is a hybrid:
 * attacks, defenses, magic and the Matrix go out as variables, while the skill
 * list and the odd tests go out as plain numbers, exactly as Cocofolia has
 * them. `docs/plans/udonarium-export-plan.md` has the field map.
 *
 * Dice are BCDice `ShadowRun5`, the same dicebot the Cocofolia palette targets.
 */

export { type PortraitEntry, type UdonariumOptions, slotTag, xmlEscape } from "./shared";
export { buildUdonariumPalette } from "./palette";
export { buildUdonariumXml, portraitEntry } from "./piece";
export { buildUdonariumConjured, buildSpiritPieces, buildSpritePieces } from "./spirits";
export { buildUdonariumVehicles, buildVehiclePieces } from "./vehicles";
