/**
 * The pieces every Udonarium module builds with: XML escaping, the chat
 * palette's variable syntax, and the `<character>` envelope a piece goes in.
 *
 * See `index.ts` for what the export is and `docs/plans/udonarium-export-plan.md`
 * for the field map.
 */
import { type Locale, type UiFn, translate } from "@/lib/i18n";
import type { ZipEntry } from "@/lib/zip";

export const uiFor =
  (locale: Locale): UiFn =>
  (key, vars) =>
    translate(locale, key, vars);

/**
 * A picture, as Udonarium carries one.
 *
 * It does not reference an image by name: the `imageIdentifier` in a piece is
 * the SHA-256 of the file's bytes, and the file travels in the same zip named
 * after that hash. Two pieces sharing a picture therefore share one copy, and
 * a picture already in the room is recognised rather than loaded twice.
 * Confirmed against udonarium.app 1.17.4.
 */
export type PortraitEntry = {
  identifier: string;
  file: ZipEntry;
};

export type UdonariumOptions = {
  /** Also list every active skill the runner can default on (SR5 p.130),
   *  plus the knowledge skills they actually have. */
  untrained?: boolean;
  /** The piece's picture, as {@link portraitEntry} resolved it. Without one
   *  the piece gets Udonarium's blank silhouette. */
  image?: PortraitEntry | null;
};

/** The attributes that get a palette variable, in the order Chummer prints
 *  them. MAG and RES only when the character has them. */
export const ATTR_ORDER = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"] as const;

/** `A`, `B`, … `Z`, `AA`, `AB`, … — the suffix that tells one weapon's set of
 *  variables from the next. The template has a fixed A/B pair; a real
 *  character carries as many weapons as it likes. */
export function slotTag(i: number): string {
  let n = i;
  let out = "";
  do {
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return out;
}

/** XML text and attribute values. Udonarium's parser is a browser's, so the
 *  five predefined entities are all it knows — and weapon names really do
 *  carry `&` (`Ares S-III Super Squirt`) and quotes. */
export function xmlEscape(s: string): string {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/** A palette variable name has to survive being written as `//name=value` and
 *  read back as `{name}`, so it cannot contain the characters that delimit
 *  either. Weapon and spell names go in values, not names, but a skill's
 *  translated name becomes a variable name. */
export const varName = (s: string) => String(s ?? "").replace(/[{}=/\s]+/g, "");

export type Lines = string[];

/** Both halves of the palette: the rolls that reference variables and the
 *  definitions that give them values. They are emitted per section — rolls
 *  first, then the `//` block they read — so a section can be dropped whole
 *  when the character has nothing in it. */
export class Section {
  rolls: Lines = [];
  defs: Lines = [];
  def(name: string, value: string | number) {
    this.defs.push(`//${varName(name)}=${value}`);
  }
  roll(expr: string, label: string) {
    this.rolls.push(`${expr} ${label}`);
  }
  get empty() {
    return !this.rolls.length;
  }
  text(heading?: string) {
    const parts = [heading, this.rolls.join("\n"), this.defs.join("\n")].filter(Boolean);
    return parts.join("\n\n");
  }
}

/** `<data name="…" type="numberResource" currentValue="v">max</data>` */
export const resource = (name: string, current: number, max: number) =>
  `        <data name="${xmlEscape(name)}" type="numberResource" currentValue="${current}">${max}</data>`;

/**
 * Where a piece lands on the table.
 *
 * Udonarium drops a piece exactly where the file says, so writing them all at
 * one spot leaves a party loaded one file at a time in a single stack.
 * Hashing the name spreads them over a small grid and keeps the export
 * reproducible — the same character always writes the same file — putting two
 * pieces in one place only when their names collide.
 */
export function spotFor(name: string): { x: number; y: number } {
  let h = 0;
  for (const c of name || "") h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return { x: 200 + (h % 6) * 100, y: 50 + (Math.floor(h / 6) % 4) * 100 };
}

/**
 * The envelope every piece shares: the placement and display attributes, the
 * name, the `detail` panels of counters, and the chat palette.
 *
 * A runner, a bound spirit and a registered sprite differ only in what goes
 * in the panels and the palette, so the XML around them is written once.
 */
export function pieceXml(piece: {
  name: string;
  panels: { title: string; rows: string[] }[];
  buffLabel: string;
  palette: string;
  /** The identifier of a picture carried in the same zip, or nothing for
   *  Udonarium's blank silhouette. */
  image?: string | null;
}): string {
  const spot = spotFor(piece.name);
  const panels = piece.panels
    .filter((p) => p.rows.length)
    .map((p) => `      <data name="${xmlEscape(p.title)}">\n${p.rows.join("\n")}\n      </data>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<character location.name="table" location.x="${spot.x}" location.y="${spot.y}" posZ="0" rotate="0" roll="0" isAltitudeIndicate="true" isLock="false" isDropShadow="false" hideInventory="false" nonTalkFlag="false" overViewWidth="270" overViewMaxHeight="250" specifyKomaImageFlag="false" komaImageHeignt="100" chatColorCode.0="#000000" chatColorCode.1="#FF0000" chatColorCode.2="#0099FF" syncDummyCounter="0">
  <data name="character">
    <data name="image">
      <data type="image" name="imageIdentifier">${xmlEscape(piece.image || "none_icon")}</data>
    </data>
    <data name="common">
      <data name="name">${xmlEscape(piece.name)}</data>
      <data name="size">2</data>
      <data name="altitude">0</data>
    </data>
    <data name="detail">
${panels}
    </data>
    <data name="buff">
      <data name="${xmlEscape(piece.buffLabel)}"></data>
    </data>
  </data>
  <chat-palette dicebot="ShadowRun5">${xmlEscape(piece.palette)}</chat-palette>
</character>
`;
}

/** The box-ticking damage track the template keeps beside the monitors.
 *  A monitor the piece does not have is left out rather than written as a
 *  bare label with no boxes — a vehicle has no stun track. */
export function woundTrack(ui: UiFn, physical: number, stun: number, core = false): string {
  const boxes = (n: number) => "[]".repeat(Math.max(n, 0));
  const text = [
    physical > 0 ? `${ui(core ? "udo.woundCore" : "udo.woundPhysical")}${boxes(physical)}` : "",
    stun > 0 ? `${ui("udo.woundStun")}${boxes(stun)}` : "",
  ]
    .filter(Boolean)
    .join("\n");
  return `        <data name="${xmlEscape(ui("udo.woundTrack"))}" type="markdown">${xmlEscape(text)}</data>`;
}
