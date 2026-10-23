"use client";

import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { actionLabel } from "@/lib/character/action-labels";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";
import { qualityExtras } from "@/lib/character/quality-extras";
import { qualityPlaceholder } from "@/lib/character/quality-placeholder";
import { AddSpiritSlots } from "@/components/character/tabs/qualities/extras/AddSpiritSlots";
import { AttributeChoiceSlots } from "@/components/character/tabs/qualities/extras/AttributeChoiceSlots";
import { BlackMarketPipeline } from "@/components/character/tabs/qualities/extras/BlackMarketPipeline";
import {
  ExtraRow,
  ExtraSelect,
  ExtraText,
} from "@/components/character/tabs/qualities/extras/controls";

type CatalogQuality = Catalog["qualities"][number];

/**
 * What one quality still leaves to decide, as a control.
 *
 * A quality's `extra_kind` says what it chooses — a target, an attribute, a
 * skill group, a Matrix action, a spirit — and this picks the control for it.
 * Most kinds are one dropdown, some pair it with a free-text box for the
 * targets no book enumerates, and three are involved enough to live in their
 * own file. Everything is stored in `quality_extras` through
 * `qualityExtras`, which is also where the key naming lives.
 *
 * `null` for the many qualities that choose nothing.
 */
export function QualityExtraEditor({
  q,
  ch,
  d,
  tr,
  trGroup,
  t,
  ui,
  patch,
  setCharacter,
  catalog,
  catalogById,
}: {
  q: {
    id: string;
    name: string;
    needs_extra?: boolean;
    extra_key?: string;
    extra_kind?: string | null;
    select_options?: string[];
    spirit_options?: string[];
    expertise_skill?: string;
    add_spirit_count?: number;
    selectside?: boolean;
  };
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  trGroup: (group: string) => string;
  t: (key: string, fallback?: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  setCharacter: (next: Character) => void;
  catalog: Catalog;
  catalogById: Map<string, CatalogQuality>;
}) {
  /**
   * Every control below is one row of the quality list, and its only visible
   * cue is the placeholder option ("対象を選択"). That is not an accessible
   * name, so a character with a dozen qualities that take a target announces
   * a dozen identical comboboxes. Naming each one after its quality
   * ("Allergy: 対象を選択") is what makes the panel navigable.
   */
  const named = (prompt: string) => `${tr(q.name)}: ${prompt}`;
  const extras = qualityExtras(ch, patch, setCharacter);
  const spec = catalogById.get(q.id);

  const kind =
    q.extra_kind ||
    spec?.extra_kind ||
    (q.name === "Exceptional Attribute"
      ? "attribute"
      : q.selectside
        ? "side"
        : q.needs_extra
          ? "text"
          : null);
  const options = q.select_options?.length ? q.select_options : spec?.select_options || [];
  const attributeChoices = spec?.attribute_choices || [];
  const addSpiritPicks = (d.add_spirit_picks || []).filter((row) => row.quality_id === q.id);

  if (attributeChoices.length) {
    return (
      <AttributeChoiceSlots
        q={q}
        ch={ch}
        d={d}
        t={t}
        ui={ui}
        patch={patch}
        named={named}
        choices={attributeChoices}
      />
    );
  }
  if (kind === "add_spirit" || addSpiritPicks.length) {
    return (
      <AddSpiritSlots
        q={q}
        ch={ch}
        d={d}
        tr={tr}
        ui={ui}
        patch={patch}
        named={named}
        catalog={catalog}
        count={q.add_spirit_count || spec?.add_spirit_count || 1}
      />
    );
  }
  if (q.name === "Black Market Pipeline") {
    return <BlackMarketPipeline q={q} ch={ch} d={d} tr={tr} ui={ui} patch={patch} named={named} />;
  }
  if (kind === "side" || q.selectside) {
    return (
      <ExtraSelect
        extras={extras}
        storeKey={q.id}
        named={named}
        prompt={ui("quality.side")}
        options={["Left", "Right"]}
        label={(side) => ui(side === "Left" ? "common.left" : "common.right")}
      />
    );
  }
  if (kind === "matrix_action") {
    return (
      <ExtraRow>
        <ExtraSelect
          extras={extras}
          storeKey={q.id}
          named={named}
          prompt={ui("quality.matrixAction")}
          options={options}
          label={(name) => actionLabel(name, ui, tr)}
          strict
        />
        {/* the catalog list is not exhaustive; "または手入力" alone says
            nothing about what is being typed */}
        <ExtraText
          extras={extras}
          storeKey={q.id}
          placeholder={ui("quality.orType")}
          name={named(ui("quality.matrixActionFree"))}
        />
      </ExtraRow>
    );
  }
  if (kind === "expertise") {
    const skillName = q.expertise_skill || spec?.expertise_skill || "";
    const known = options.length
      ? options
      : catalog.skills.skills.find((s) => s.name === skillName)?.specs || [];
    const prompt = skillName
      ? ui("quality.expertise", { skill: skillName })
      : ui("quality.expertiseAny");
    return (
      <ExtraRow>
        <ExtraSelect
          extras={extras}
          storeKey={q.id}
          named={named}
          prompt={prompt}
          options={known}
          label={tr}
          strict
        />
        <ExtraText
          extras={extras}
          storeKey={q.id}
          placeholder={ui("quality.orType")}
          name={named(ui("quality.expertiseFree"))}
        />
        <span className="muted">{ui("quality.expertiseNote")}</span>
      </ExtraRow>
    );
  }
  if (kind === "weapon_skill") {
    return (
      <ExtraSelect
        extras={extras}
        storeKey={q.id}
        named={named}
        prompt={ui("quality.weaponSkill")}
        options={options}
        label={tr}
      />
    );
  }
  if (kind === "spell_category" || kind === "spell_spirit_category" || kind === "spirit_category") {
    // Two choices for one quality, so the spirit half gets its own key —
    // except where the spirit is the only choice and takes the bare id.
    const spiritKey = kind === "spirit_category" ? q.id : `${q.id}:spiritcategory`;
    const spirits = q.spirit_options?.length ? q.spirit_options : spec?.spirit_options || [];
    return (
      <ExtraRow>
        {kind !== "spirit_category" ? (
          <ExtraSelect
            extras={extras}
            storeKey={q.id}
            named={named}
            prompt={ui("quality.spellCategory")}
            options={options}
            label={tr}
          />
        ) : null}
        {kind !== "spell_category" ? (
          <ExtraSelect
            extras={extras}
            storeKey={spiritKey}
            named={named}
            prompt={ui("quality.spirit")}
            options={spirits}
            label={tr}
          />
        ) : null}
      </ExtraRow>
    );
  }
  if (kind === "quality") {
    return (
      <ExtraSelect
        extras={extras}
        storeKey={q.id}
        named={named}
        prompt={ui("quality.attachedQuality")}
        options={options}
        label={tr}
      />
    );
  }
  if (kind === "skillgroup") {
    return (
      <ExtraSelect
        extras={extras}
        storeKey={q.id}
        named={named}
        prompt={ui("quality.skillGroup")}
        options={catalog.skills.groups || []}
        label={trGroup}
      />
    );
  }
  if (kind === "attribute" || q.name === "Exceptional Attribute") {
    return (
      <ExtraSelect
        extras={extras}
        storeKey={q.id}
        named={named}
        prompt={ui("quality.attribute")}
        options={ATTRS.filter(
          (key) => key !== "EDG" && key !== "MAG" && key !== "RES" && key !== "DEP",
        )}
        label={(key) => attrLabel(key, t)}
      />
    );
  }
  if (kind === "text" || q.needs_extra) {
    // Records on File taken twice: each take keeps its own text
    const textKey = q.extra_key ?? q.id;
    if (!options.length) {
      // what the box is for varies by quality — an allergen, a drug, a code
      // of honour — and a single prompt named one quality's examples for all
      const prompt = ui(qualityPlaceholder(q.name));
      return (
        <ExtraText extras={extras} storeKey={textKey} placeholder={prompt} name={named(prompt)} />
      );
    }
    return (
      <ExtraRow>
        <ExtraSelect
          extras={extras}
          storeKey={textKey}
          named={named}
          prompt={ui("quality.target")}
          options={options}
          label={tr}
          strict
        />
        <ExtraText
          extras={extras}
          storeKey={textKey}
          placeholder={ui("quality.orType")}
          name={named(ui("quality.targetFree"))}
        />
      </ExtraRow>
    );
  }
  return null;
}
