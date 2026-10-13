"use client";

import { useState } from "react";
import type { Character, CharacterSettings, SettingsPreset } from "@/lib/types";
import { buildMethodPatch } from "@/lib/character/build-method";
import {
  loadSettingsFiles,
  removeSettingsFile,
  saveSettingsFile,
} from "@/lib/character/settings-store";
import { api, type MergeResult } from "@/lib/api";
import {
  CustomDataShapeError,
  readStyleFolder,
  readStyleZip,
  recallFolder,
  rememberFolder,
  type CustomDataFiles,
  type StyleFolder,
} from "@/lib/character/customdata-store";
import { ZipError } from "@/lib/character/zip";
import { errorMessage } from "@/lib/errors";
import type { UiFn } from "@/lib/i18n";

/**
 * The settings a preset changes. Only the knobs it moves off the printed SR5
 * values are written — the same rule the .chum5 import follows — so Standard
 * stays a bare `{name, books}`. Without them, picking Prime Runner kept
 * Standard's priority rows, quality cap and 10-point karma-to-nuyen cap.
 */
export function presetSettings(preset: SettingsPreset): CharacterSettings {
  const out: CharacterSettings = { name: preset.name, books: [...preset.books] };
  if (preset.priority_table && preset.priority_table !== "Standard") {
    out.priority_table = preset.priority_table;
  }
  if (preset.quality_karma_limit != null && preset.quality_karma_limit !== 25) {
    out.quality_karma_limit = preset.quality_karma_limit;
  }
  if (preset.nuyen_max_bp != null && preset.nuyen_max_bp !== 10) {
    out.priority_karma_nuyen_base = preset.nuyen_max_bp;
  }
  return out;
}

/**
 * Getting a ruleset into the character: where it comes from, what its custom
 * data does, and what went wrong.
 *
 * All of it is asynchronous and none of it is visible — a pick parses a file,
 * uploads the directories it names, waits for the dataset hash and only then
 * patches the character — so it sits here rather than among the pulldown's
 * JSX. What the panel renders from it is the three pieces of state: the
 * settings files this browser knows, the last merge's report, and the error.
 */
export function useRulesetLoader({
  character: ch,
  presets,
  ui,
  patch,
}: {
  character: Character;
  presets: SettingsPreset[];
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
}) {
  const [merge, setMerge] = useState<MergeResult | null>(null);
  // The last folder's files, so a second ruleset from the same pick merges
  // without another trip through the file dialog. Null until one is picked or
  // `recallFolder` finds the previous session's.
  const [folder, setFolder] = useState<CustomDataFiles | null>(null);
  // Read once, lazily — the same shape as `useSheetLayout`. `loadSettingsFiles`
  // swallows a missing / disabled store, so a prerender just sees none.
  const [files, setFiles] = useState<CharacterSettings[]>(loadSettingsFiles);
  const [error, setError] = useState<string | null>(null);

  /**
   * Apply a ruleset, merging its custom data when the folder is already here.
   *
   * The dataset hash is per settings file, not per folder: two files in one
   * pick enable different directories, so each needs its own merge. Waiting
   * for it keeps the character from being patched twice.
   */
  async function apply(
    settings: CharacterSettings,
    method?: string | null,
    /** The custom data in hand, when a pick just produced it. Otherwise the
     *  one from the last pick is found again. `folder` is React state, so a
     *  pick cannot read back what it set a line earlier. */
    picked?: CustomDataFiles,
  ): Promise<void> {
    const base = { ...(method ? buildMethodPatch(method, ch) : {}) };
    const wanted = settings.customdata || [];
    const have = wanted.length > 0 ? (picked ?? folder ?? (await recallFolder())) : null;
    if (!have) {
      await patch({ ...base, settings });
      return;
    }
    setFolder(have);
    try {
      await patch({ ...base, settings: { ...settings, ...(await merged(have, wanted)) } });
    } catch (e) {
      // The ruleset still applies — it is the custom data that did not, and
      // the missing-data line in the panel says so.
      await patch({ ...base, settings });
      setError(errorMessage(e, ui, "settings.customDataFailed"));
    }
  }

  /** Merge `wanted` out of `have` and report it. Returns the hash to carry. */
  async function merged(have: CustomDataFiles, wanted: string[]): Promise<{ dataset: string }> {
    const res = await api.uploadCustomData(have, wanted);
    setMerge(res);
    return { dataset: res.dataset };
  }

  function onPick(picked: string) {
    if (!picked) {
      // Back to unrestricted, and back to the printed SR5 numbers: a bare
      // `{name, books}` leaves every knob unset, which is what unset means.
      void patch({ settings: { name: "", books: [] } });
      return;
    }
    setError(null);
    setMerge(null);
    const file = files.find((f) => f.name === picked);
    if (file) {
      void apply(file);
      return;
    }
    const preset = presets.find((p) => p.name === picked);
    if (preset) void apply(presetSettings(preset), preset.build_method);
  }

  /** One picked file: a settings `.xml`, or a `.zip` of the whole folder. */
  async function onFile(file: File) {
    if (file.name.toLowerCase().endsWith(".zip")) {
      await onZip(file);
      return;
    }
    setError(null);
    setMerge(null);
    try {
      const { settings, build_method } = await api.parseSettings(await file.arrayBuffer());
      setFiles(saveSettingsFile(settings));
      await apply(settings, build_method);
    } catch (e) {
      setError(errorMessage(e, ui, "settings.loadFailed"));
    }
  }

  /**
   * The same folder, zipped.
   *
   * Android's Chrome does not implement `webkitdirectory`, so on a phone the
   * folder button opens nothing usable and a ruleset that names custom data
   * cannot be loaded at all. A zip goes through an ordinary file input, which
   * every browser has.
   */
  async function onZip(file: File) {
    setError(null);
    setMerge(null);
    try {
      await applyStyle(await readStyleZip(await file.arrayBuffer()));
    } catch (e) {
      setError(
        e instanceof ZipError
          ? ui(e.reason === "not-a-zip" ? "settings.zipNotAZip" : "settings.zipUnsupported")
          : styleError(e),
      );
    }
  }

  /**
   * A whole ruleset folder: every settings file in it, and the custom data.
   *
   * All of the settings files join the pulldown, because that is what the
   * folder offers — but only one can be applied, and picking for the user
   * would be a guess. One file applies itself; several leave the choice in
   * the pulldown, with the folder already here so the choice merges.
   */
  async function onFolder(list: readonly File[]) {
    setError(null);
    setMerge(null);
    try {
      await applyStyle(await readStyleFolder(list));
    } catch (e) {
      setError(styleError(e));
    }
  }

  /** A ruleset that arrived whole, however it arrived. */
  async function applyStyle(pick: StyleFolder) {
    // An empty object is "this pick had no custom data", not "here is none" —
    // passing it on would shadow the folder from the previous pick.
    const picked = Object.keys(pick.customdata).length > 0 ? pick.customdata : undefined;
    if (picked) {
      setFolder(picked);
      await rememberFolder(picked);
    }
    let loaded: CharacterSettings[] = [];
    let first: { settings: CharacterSettings; build_method: string | null } | null = null;
    for (const file of pick.settings) {
      const parsed = await api.parseSettings(new TextEncoder().encode(file.text).buffer);
      loaded = saveSettingsFile(parsed.settings);
      first ??= parsed;
    }
    if (loaded.length > 0) setFiles(loaded);
    if (pick.settings.length === 1 && first) {
      await apply(first.settings, first.build_method, picked);
      return;
    }
    // No settings half — a bare `customdata/` pick for the ruleset already
    // applied, which is the pre-folder way of doing it and still works.
    const wanted = ch.settings?.customdata || [];
    if (pick.settings.length === 0 && wanted.length > 0) {
      await patch({
        settings: {
          ...(ch.settings || { name: "", books: [] }),
          ...(await merged(pick.customdata, wanted)),
        },
      });
    }
  }

  function styleError(e: unknown): string {
    return e instanceof CustomDataShapeError
      ? ui("settings.customDataNotAFolder")
      : errorMessage(e, ui, "settings.customDataFailed");
  }

  function onForget(target: string) {
    setFiles(removeSettingsFile(target));
    if (ch.settings?.name === target) void patch({ settings: { name: "", books: [] } });
  }

  return { files, error, merge, onPick, onFile, onFolder, onForget };
}
