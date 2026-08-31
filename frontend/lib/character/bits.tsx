import type { ReactNode } from "react";

export function skillsoftBit(rating?: number) {
  if (!rating) return null;
  return <span className="muted"> ソフトR{rating}</span>;
}

export function specBit(spec?: string | null, label?: string, bonus: number = 2) {
  if (!spec) return null;
  return (
    <span className="muted" title={label || spec}>
      {" "}
      専門+{bonus}
    </span>
  );
}
