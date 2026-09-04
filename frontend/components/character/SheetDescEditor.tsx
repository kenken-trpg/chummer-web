import type { Character } from "@/lib/types";
import { type MsgKey, useUiText } from "@/lib/i18n";

export function SheetDescEditor({
  ch,
  patch,
  onPortraitFile,
}: {
  ch: Character;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  onPortraitFile: (file: File) => void | Promise<void>;
}) {
  const { ui } = useUiText();
  return (
    <div className="no-print sheet-notes-edit">
      {/* a heading for the whole editor, not a label for one control */}
      <h4 className="field-label">{ui("desc.title")}</h4>
      <div className="portrait-edit">
        {ch.portrait ? (
          <img className="portrait-thumb" src={ch.portrait} alt={ui("desc.portraitAlt")} />
        ) : (
          <div className="portrait-thumb portrait-empty">{ui("desc.noImage")}</div>
        )}
        <div className="portrait-edit-controls">
          <input
            type="file"
            accept="image/*"
            aria-label={ui("desc.pickPortrait")}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onPortraitFile(f);
              e.target.value = "";
            }}
          />
          {ch.portrait ? (
            <button className="btn" type="button" onClick={() => void patch({ portrait: "" })}>
              {ui("desc.removeImage")}
            </button>
          ) : null}
          <span className="muted">{ui("desc.portraitNote")}</span>
        </div>
      </div>
      <div className="sheet-desc-grid">
        {(
          [
            ["age", "desc.age"],
            ["sex", "desc.sex"],
            ["height", "desc.height"],
            ["weight", "desc.weight"],
            ["eyes", "desc.eyes"],
            ["hair", "desc.hair"],
            ["skin", "desc.skin"],
            ["concept", "desc.concept"],
          ] as const satisfies readonly (readonly [keyof Character, MsgKey])[]
        ).map(([field, label]) => (
          <label key={field}>
            {ui(label)}
            <input
              defaultValue={(ch[field] as string) || ""}
              key={`${ch.id}-${field}`}
              onBlur={(e) => {
                if ((e.target.value || "") !== ((ch[field] as string) || ""))
                  patch({ [field]: e.target.value });
              }}
            />
          </label>
        ))}
      </div>
      {(
        [
          ["appearance", "desc.appearance"],
          ["background", "desc.background"],
          ["notes", "desc.notes"],
        ] as const satisfies readonly (readonly [keyof Character, MsgKey])[]
      ).map(([field, label]) => (
        <div key={field} className="sheet-notes-edit" style={{ margin: "8px 0 0" }}>
          <label>
            {ui(label)}
            <textarea
              rows={field === "notes" ? 3 : 2}
              defaultValue={(ch[field] as string) || ""}
              key={`${ch.id}-${field}`}
              placeholder={field === "notes" ? ui("desc.notesPlaceholder") : ""}
              onBlur={(e) => {
                if ((e.target.value || "") !== ((ch[field] as string) || ""))
                  patch({ [field]: e.target.value });
              }}
            />
          </label>
        </div>
      ))}
    </div>
  );
}
