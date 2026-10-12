"use client";
import { useId, useRef, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import type { LifeModuleCatalogItem } from "@/lib/types/catalog";
import {
  lifeModuleAlreadyTaken,
  lifeModuleRequirementsMet,
  lifeModuleRequirementText,
} from "@/lib/character/life-modules";

type Props = Pick<TabPanelProps, "catalog" | "character" | "ui" | "patch"> & {
  stage: string;
  candidates: LifeModuleCatalogItem[];
  taken: boolean;
  repeatable: boolean;
};

export function LifeModulePicker({
  stage,
  candidates,
  taken,
  repeatable,
  catalog,
  character,
  ui,
  patch,
}: Props) {
  const groupId = useId();
  const [previewId, setPreviewId] = useState("");
  const [busy, setBusy] = useState(false);
  const adding = useRef(false);
  // A search or rulebook change can hide the previewed row. Only a current
  // candidate can be added, even if its ID is still in local state.
  const preview = candidates.find((row) => row.id === previewId);
  const met = preview
    ? lifeModuleRequirementsMet(preview.required || [], character, catalog)
    : false;
  const full = taken && !repeatable;
  const duplicate = !!preview && lifeModuleAlreadyTaken(preview, character, catalog);
  const canAdd =
    !!preview && !preview.unsupported.length && met && !full && !duplicate && !character.career;

  async function add() {
    if (!canAdd || adding.current || !preview) return;
    adding.current = true;
    setBusy(true);
    try {
      await patch({ life_modules: [...(character.life_modules || []), preview.id] });
      setPreviewId("");
    } finally {
      adding.current = false;
      setBusy(false);
    }
  }

  return (
    <fieldset className="life-picker" disabled={character.career || busy}>
      <legend>
        {stage}: {ui("life.pick")}
      </legend>
      <p className="muted">{ui("life.browseHint")}</p>
      <div className="life-browser">
        <div
          className="life-candidates"
          role="region"
          aria-label={`${stage}: ${ui("life.candidates")}`}
        >
          {candidates.map((row) => {
            const allowed =
              !row.unsupported.length &&
              !lifeModuleAlreadyTaken(row, character, catalog) &&
              lifeModuleRequirementsMet(row.required || [], character, catalog);
            return (
              <label
                className={`life-candidate${preview?.id === row.id ? " selected" : ""}`}
                key={row.id}
              >
                <input
                  type="radio"
                  name={groupId}
                  value={row.id}
                  checked={preview?.id === row.id}
                  onChange={() => setPreviewId(row.id)}
                  aria-controls={`${groupId}-preview`}
                />
                <span>
                  <strong>{row.name}</strong>
                  {row.parent && <span className="muted">{row.parent}</span>}
                  <span className="muted">
                    {row.karma} Karma · {row.source} {row.page}
                  </span>
                  {!!row.required?.length && (
                    <span>
                      {ui("life.requires", {
                        requirements: lifeModuleRequirementText(row.required),
                      })}
                    </span>
                  )}
                  {lifeModuleAlreadyTaken(row, character, catalog) && (
                    <span className="warn">{ui("life.alreadyTaken")}</span>
                  )}
                  {!allowed && <span className="warn">{ui("life.unavailable")}</span>}
                </span>
              </label>
            );
          })}
        </div>
        <div className="life-preview" id={`${groupId}-preview`}>
          {preview ? (
            <>
              <h4>{preview.name}</h4>
              {preview.parent && <p className="muted">{preview.parent}</p>}
              <p>
                {preview.karma} Karma · {preview.source} {preview.page}
              </p>
              {preview.story && <p className="life-preview-story">{preview.story}</p>}
              {!!preview.required?.length && (
                <p className={met ? "muted" : "error"}>
                  {ui("life.requires", {
                    requirements: lifeModuleRequirementText(preview.required),
                  })}
                  {!met && ` — ${ui("life.requirementUnmet")}`}
                </p>
              )}
              {!!preview.unsupported.length && <p className="error">{ui("life.unsupported")}</p>}
              <p>{ui("life.choiceCount", { count: preview.choices.length })}</p>
              {!!preview.nuyen && <p>{ui("life.nuyen", { amount: preview.nuyen })}</p>}
              {preview.free_positive_qualities || preview.free_negative_qualities ? (
                <p>
                  {ui("life.freeQuality", {
                    positive: preview.free_positive_qualities,
                    negative: preview.free_negative_qualities,
                  })}
                </p>
              ) : null}
            </>
          ) : (
            <p className="muted">{ui("life.previewHint")}</p>
          )}
          {full && <p className="muted">{ui("life.stageFull")}</p>}
          <button
            type="button"
            className="life-add"
            disabled={!canAdd || busy}
            onClick={() => void add()}
          >
            {ui("life.add")}
          </button>
        </div>
      </div>
    </fieldset>
  );
}
