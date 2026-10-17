/** The runner's own piece — the palette wrapped in Udonarium's `data.xml`,
 *  with the portrait and the condition monitors. */
import type { Catalog, Character, Derived } from "@/lib/types";
import { buildUdonariumPalette } from "./palette";
import { type Locale } from "@/lib/i18n";
import {
  type PortraitEntry,
  type UdonariumOptions,
  pieceXml,
  woundTrack,
  resource,
  uiFor,
} from "./shared";

const PORTRAIT_EXT: Record<string, string> = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/gif": "gif",
  "image/webp": "webp",
};

/**
 * Turn a stored `data:` portrait into the file and identifier a piece needs.
 *
 * Returns null for anything that is not one of the image types a portrait is
 * allowed to be (`PORTRAIT_TYPES`), or that does not decode — a picture that
 * cannot be carried is not a reason to fail the export, it just leaves the
 * piece with the blank silhouette.
 */
export async function portraitEntry(dataUrl: string): Promise<PortraitEntry | null> {
  const m = /^data:([^;,]+);base64,([\s\S]*)$/.exec(dataUrl || "");
  const ext = m && PORTRAIT_EXT[m[1].trim().toLowerCase()];
  if (!m || !ext) return null;
  // the explicit buffer type is what `crypto.subtle.digest` takes
  let bytes: Uint8Array<ArrayBuffer>;
  try {
    const bin = atob(m[2]);
    bytes = new Uint8Array(new ArrayBuffer(bin.length));
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  } catch {
    return null;
  }
  if (!bytes.length) return null;
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const identifier = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return { identifier, file: { name: `${identifier}.${ext}`, content: bytes } };
}

/**
 * The whole `data.xml` for one Udonarium character piece.
 *
 * The `detail` panel carries only the resources the table clicks during play —
 * the condition monitors, Edge and the movement left this turn. Everything the
 * character *is* lives in the palette's variables, which is where the table can
 * reach it, so it is not duplicated here.
 */
export function buildUdonariumXml(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
  opts: UdonariumOptions = {},
): string {
  const ui = uiFor(locale);
  const d: Derived = ch.derived;
  const cm = d.condition_monitor || { physical: 0, stun: 0 };
  const edge = d.totals?.EDG || 0;
  // A persona's Matrix condition monitor is 8 + half its Device Rating,
  // rounded up (SR5 p.228) — and a technomancer has one too, off the living
  // persona, which is why this asks the same question the palette's Matrix
  // block does rather than only looking for a deck.
  const donglelink = d.commlink && (d.commlink.attack || d.commlink.sleaze) ? d.commlink : null;
  const persona = d.cyberdeck || d.living_persona || donglelink;
  const matrixCm = persona ? 8 + Math.ceil((persona.device_rating || 1) / 2) : 0;
  // `movement.run` is Chummer's metres-per-Complex-Action string; a rating
  // modifier can leave it non-numeric, and then the piece starts at 0.
  const parsed = Number.parseInt(String(d.movement?.run ?? ""), 10);
  const run = Number.isFinite(parsed) ? parsed : 0;

  return pieceXml({
    name: ch.name || tr(ch.metatype) || "Runner",
    image: opts.image?.identifier,
    buffLabel: ui("udo.panelBuff"),
    palette: buildUdonariumPalette(ch, catalog, tr, locale, opts),
    panels: [
      {
        title: ui("udo.panelStatus"),
        rows: [
          resource(ui("coco.initiative"), 0, 0),
          resource(ui("coco.edge"), edge, edge),
          resource(ui("udo.movementLeft"), run, run),
        ],
      },
      {
        title: ui("udo.panelCm"),
        rows: [
          // an A.I. has a Core track in place of both
          ...(cm.core
            ? [resource(ui("coco.cmCore"), 0, cm.physical)]
            : [
                resource(ui("coco.cmPhysical"), 0, cm.physical),
                resource(ui("coco.cmStun"), 0, cm.stun),
              ]),
          ...(matrixCm ? [resource(ui("coco.cmMatrix"), 0, matrixCm)] : []),
          woundTrack(ui, cm.physical, cm.stun, cm.core),
        ],
      },
    ],
  });
}
