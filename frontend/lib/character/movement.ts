import type { Derived } from "@/lib/types/derived";
import type { UiFn } from "@/lib/i18n";

/** Ground keeps its established display; other available media supplement it. */
export function otherMovementRows(movement: Derived["movement"], ui: UiFn) {
  return (["Swim", "Fly"] as const).flatMap((category) => {
    const mode = movement.modes?.[category];
    if (!mode?.available) return [];
    const distances = [mode.walk, mode.run].filter((value) => Number(value) !== 0);
    const parts = [(distances.length ? distances : ["0"]).map((value) => `${value}m`).join(" / ")];
    if (Number(mode.sprint) !== 0) parts.push(ui("sheet.movementPerHit", { sprint: mode.sprint }));
    return [
      { label: ui(category === "Swim" ? "sheet.swim" : "sheet.fly"), value: parts.join(" / ") },
    ];
  });
}
