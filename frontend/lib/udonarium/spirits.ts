/** Bound spirits and registered sprites, each as a piece of its own. */
import type { Catalog, Character } from "@/lib/types";
import { attrName, makeT } from "@/lib/ui-strings";
import { renderNotice } from "@/lib/engine-notices";
import { type Locale } from "@/lib/i18n";
import { skillLabel } from "@/lib/character/format";
import { woundTrack, Section, pieceXml, resource, uiFor, varName } from "./shared";

// --- bound spirits and registered sprites, as their own pieces -------------
// A bound spirit or a registered sprite is dropped on the table and run like
// anything else there, so it gets a piece of its own — the same thing the
// Cocofolia export does with `buildCocofoliaConjured`.
//
// Force (or Level) is the variable worth having here. Every limit on the
// sheet is it, and raising it at the table is the one adjustment that comes
// up, so the rolls reference it rather than the number it happened to be at
// export time. The attributes it already determined stay as they are: nothing
// recomputes them when the variable moves.

const SPIRIT_ATTRS = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"] as const;

/** One piece per bound spirit. Skill test = Force + linked attribute,
 *  limit = Force (SR5 p.395). */
export function buildSpiritPieces(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; xml: string }[] {
  const ui = uiFor(locale);
  const t = makeT(catalog, locale);
  const A = (k: string) => varName(attrName(k, t));
  const forceVar = varName(ui("udo.varForce"));

  return (ch.derived.spirits || [])
    .filter((s) => s.bound)
    .map((s) => {
      const a = s.attributes || {};
      const force = s.force || 1;
      const sec = new Section();

      sec.roll(`2D6+${a.INI ?? force * 2}`, ui("coco.initiative"));
      for (const sk of s.skills || []) {
        const v = varName(tr(sk.name));
        const attr = sk.attribute || "";
        sec.roll(
          `({${attr ? A(attr) : forceVar}}+{${v}}+0)B6@{${forceVar}}`,
          skillLabel(sk.name, tr),
        );
      }
      sec.roll(`({${A("REA")}}+{${A("INT")}}+0)B6`, ui("coco.defense"));
      // Immunity to Normal Weapons: Force twice over, on top of Body.
      sec.roll(`({${A("BOD")}}+{${forceVar}}+{${forceVar}})B6`, ui("coco.immunityResist"));
      sec.roll(`({${forceVar}}+{${forceVar}})B6`, ui("coco.resistBanishing"));

      sec.def(forceVar, force);
      for (const k of SPIRIT_ATTRS) if ((a[k] || 0) > 0) sec.def(A(k), a[k]);
      for (const sk of s.skills || []) sec.def(varName(tr(sk.name)), sk.rating || force);

      const powers = [...(s.powers || []), ...(s.optionalpowers || [])].map((p) => tr(p.name));
      const notes = [
        ui("coco.spiritName", {
          name: tr(s.name),
          role: s.role_label ? renderNotice(s.role_label, ui) : s.role || ui("coco.spirit"),
          force,
        }),
        ui("coco.spiritMemo", { services: s.services }),
        powers.length ? ui("coco.powers", { list: powers.join(ui("common.listSep")) }) : "",
        s.weaknesses?.length
          ? ui("coco.weaknesses", { list: s.weaknesses.map(tr).join(ui("common.listSep")) })
          : "",
        ui("coco.spiritNote"),
      ].filter(Boolean);

      const physCM = 8 + Math.ceil((a.BOD || 0) / 2);
      const stunCM = 8 + Math.ceil((a.WIL || 0) / 2);
      return {
        name: `${tr(s.name)} F${force}`,
        xml: pieceXml({
          name: `${tr(s.name)} F${force}`,
          buffLabel: ui("udo.panelBuff"),
          palette: [notes.join("\n"), sec.text()].join("\n\n"),
          panels: [
            {
              title: ui("udo.panelStatus"),
              rows: [
                resource(ui("coco.initiative"), 0, 0),
                resource(ui("udo.varForce"), force, force),
                resource(ui("udo.services"), s.services || 0, s.services || 0),
              ],
            },
            {
              title: ui("udo.panelCm"),
              rows: [
                resource(ui("coco.cmPhysical"), 0, physCM),
                resource(ui("coco.cmStun"), 0, stunCM),
                woundTrack(ui, physCM, stunCM),
              ],
            },
          ],
        }),
      };
    });
}

/** One piece per registered sprite. Skill test = Level + skill, limit = Level
 *  (SR5 p.254). */
export function buildSpritePieces(
  ch: Character,
  _catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; xml: string }[] {
  const ui = uiFor(locale);
  const levelVar = varName(ui("udo.varLevel"));
  const vFw = varName(ui("udo.varFirewall"));

  return (ch.derived.sprites || [])
    .filter((s) => s.registered)
    .map((s) => {
      const level = s.level || 1;
      const m = s.matrix || { attack: 0, sleaze: 0, dataprocessing: 0, firewall: 0, initiative: 0 };
      const sec = new Section();

      sec.roll(`${level}D6+${m.initiative || level * 2}`, ui("coco.initiative"));
      for (const sk of s.skills || []) {
        const v = varName(tr(sk.name));
        sec.roll(`({${levelVar}}+{${v}}+0)B6@{${levelVar}}`, skillLabel(sk.name, tr));
      }
      sec.roll(`({${vFw}}+{${levelVar}}+0)B6`, ui("coco.matrixDefensePlain"));
      sec.roll(`({${levelVar}}+{${levelVar}})B6`, ui("coco.resistDerez"));

      sec.def(levelVar, level);
      sec.def(varName(ui("udo.varAttack")), m.attack);
      sec.def(varName(ui("udo.varSleaze")), m.sleaze);
      sec.def(varName(ui("udo.varDataProc")), m.dataprocessing);
      sec.def(vFw, m.firewall);
      for (const sk of s.skills || []) sec.def(varName(tr(sk.name)), sk.rating || level);

      const powers = (s.powers || []).map((p) => tr(p.name));
      const notes = [
        ui("coco.spriteLevel", { name: tr(s.name), level }),
        ui("coco.spriteMemo", { services: s.services }),
        powers.length ? ui("coco.powers", { list: powers.join(ui("common.listSep")) }) : "",
        ui("coco.spriteNote"),
      ].filter(Boolean);

      const cm = 8 + Math.ceil(level / 2);
      const name = `${tr(s.name)} L${level}`;
      return {
        name,
        xml: pieceXml({
          name,
          buffLabel: ui("udo.panelBuff"),
          palette: [notes.join("\n"), sec.text()].join("\n\n"),
          panels: [
            {
              title: ui("udo.panelStatus"),
              rows: [
                resource(ui("coco.initiative"), 0, 0),
                resource(ui("udo.varLevel"), level, level),
                resource(ui("udo.tasks"), s.services || 0, s.services || 0),
              ],
            },
            {
              title: ui("udo.panelCm"),
              rows: [resource(ui("coco.cmMatrix"), 0, cm)],
            },
          ],
        }),
      };
    });
}

/**
 * Every bound spirit and registered sprite, one `.xml` per piece, ready for
 * one zip. Udonarium reads every xml an archive holds, so the whole retinue
 * goes on the table in one drop. Empty when the character has none.
 */
export function buildUdonariumConjured(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; content: string }[] {
  const pieces = [
    ...buildSpiritPieces(ch, catalog, tr, locale),
    ...buildSpritePieces(ch, catalog, tr, locale),
  ];
  // The entry names are Udonarium's to read, not the table's to see — the
  // piece's own name comes from inside the xml — so they are numbered rather
  // than named after a spirit, which keeps them ASCII and unique.
  return pieces.map((p, i) => ({ name: i ? `data_${i}.xml` : "data.xml", content: p.xml }));
}
