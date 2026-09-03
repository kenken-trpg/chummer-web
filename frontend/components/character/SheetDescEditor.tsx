import type { Character } from "@/lib/types";

export function SheetDescEditor({
  ch,
  patch,
  onPortraitFile,
}: {
  ch: Character;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  onPortraitFile: (file: File) => void | Promise<void>;
}) {
  return (
    <div className="no-print sheet-notes-edit">
      {/* a heading for the whole editor, not a label for one control */}
      <h4 className="field-label">記述</h4>
      <div className="portrait-edit">
        {ch.portrait ? (
          <img className="portrait-thumb" src={ch.portrait} alt="ポートレート" />
        ) : (
          <div className="portrait-thumb portrait-empty">画像なし</div>
        )}
        <div className="portrait-edit-controls">
          <input
            type="file"
            accept="image/*"
            aria-label="ポートレート画像を選択"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onPortraitFile(f);
              e.target.value = "";
            }}
          />
          {ch.portrait ? (
            <button className="btn" type="button" onClick={() => void patch({ portrait: "" })}>
              画像を削除
            </button>
          ) : null}
          <span className="muted">.chum5 の mugshot と相互変換。3MB まで。</span>
        </div>
      </div>
      <div className="sheet-desc-grid">
        {(
          [
            ["age", "年齢"],
            ["sex", "性別"],
            ["height", "身長"],
            ["weight", "体重"],
            ["eyes", "目"],
            ["hair", "髪"],
            ["skin", "肌"],
            ["concept", "コンセプト"],
          ] as const
        ).map(([field, label]) => (
          <label key={field}>
            {label}
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
          ["appearance", "容姿"],
          ["background", "背景"],
          ["notes", "メモ"],
        ] as const
      ).map(([field, label]) => (
        <div key={field} className="sheet-notes-edit" style={{ margin: "8px 0 0" }}>
          <label>
            {label}
            <textarea
              rows={field === "notes" ? 3 : 2}
              defaultValue={(ch[field] as string) || ""}
              key={`${ch.id}-${field}`}
              placeholder={
                field === "notes"
                  ? "GM 用メモ・運用メモなど。シートと .chum5 書き出しに反映されます。"
                  : ""
              }
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
