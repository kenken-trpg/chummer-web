import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function SinSection(s: SheetData) {
  const { tr, sins, gearChildren } = s;
  return (
    <Section title="SIN／ライセンス" empty={!sins.length}>
      <ul className="sheet-list">
        {sins.map((sin) => {
          const licenses = gearChildren(sin.id);
          return (
            <li key={sin.id}>
              <b>{tr(sin.name)}</b>
              {sin.rating > 0 ? ` R${sin.rating}` : ""}
              {sin.extra ? `（${tr(sin.extra)}）` : ""}
              {licenses.length ? (
                <span className="sheet-dim">
                  {" ・ "}
                  {licenses
                    .map(
                      (l) =>
                        `${tr(l.name)}${l.rating > 0 ? ` R${l.rating}` : ""}${l.extra ? `:${tr(l.extra)}` : ""}`,
                    )
                    .join("、")}
                </span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Section>
  );
}
