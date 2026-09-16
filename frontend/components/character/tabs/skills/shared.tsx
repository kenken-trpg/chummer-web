"use client";
import type { TabPanelProps } from "@/components/character/types";

/** The limits and mode every skills section reads, from one place. */
export function skillLimits({ character: ch, d }: Pick<TabPanelProps, "character" | "d">) {
  const skillMax = d.skill_rating_max ?? 6;
  const career = Boolean(ch.career || d.career);
  return {
    skillMax,
    knowledgeMax: d.knowledge_rating_max ?? skillMax,
    groupMax: d.skill_group_max ?? 6,
    career,
    // Priority / Sum-to-Ten creation only, as on the attributes tab: a Karma
    // build buys every level with karma already, and after creation raises are
    // billed from the baseline.
    splitKarma: !career && !d.karma_chargen?.enabled && Boolean(d.skill_karma),
    karmaSplit: d.skill_karma,
  };
}

/** "of which by karma": the top levels of a skill bought with karma. */
export function KarmaLevels({
  name,
  rating,
  levels,
  field,
  props,
}: {
  name: string;
  rating: number;
  levels: Record<string, number> | undefined;
  field: "skill_karma" | "knowledge_karma";
  props: TabPanelProps;
}) {
  const { character: ch, tr, ui, patch } = props;
  if (!skillLimits(props).splitKarma) return null;
  if (rating <= 0) return <span />;
  return (
    <label className="attr-karma" title={ui("skills.karmaHint")}>
      {ui("attrs.karmaLevels")}
      <input
        type="number"
        aria-label={`${tr(name)} ${ui("attrs.karmaLevels")}`}
        min={0}
        max={rating}
        value={levels?.[name] ?? 0}
        onChange={(e) =>
          patch({
            [field]: { ...(ch[field] || {}), [name]: Math.max(0, Number(e.target.value) || 0) },
          })
        }
      />
    </label>
  );
}

/** A specialization edit: drafted locally while typing, sent on commit. */
export function specEditor({
  character: ch,
  patch,
  setCharacter,
}: Pick<TabPanelProps, "character" | "patch" | "setCharacter">) {
  return {
    draft(name: string, value: string) {
      const next = { ...(ch.skill_specializations || {}) };
      if (value) next[name] = value;
      else delete next[name];
      setCharacter({ ...ch, skill_specializations: next });
    },
    commit(name: string, value: string) {
      const next = { ...(ch.skill_specializations || {}) };
      const trimmed = value.trim();
      if (trimmed) next[name] = trimmed;
      else delete next[name];
      setCharacter({ ...ch, skill_specializations: next });
      patch({ skill_specializations: next });
    },
  };
}

/** Knowledge-skill edits. Every one sends the three fields together, since
 *  the engine reads a rating, a native flag and a category as one choice. */
export function knowledgeEditor({
  catalog,
  character: ch,
  d,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "patch">) {
  const owned = new Set((d.knowledge_skills || []).map((row) => row.name));

  function send(next: {
    knowledge_skills?: Record<string, number>;
    native_languages?: string[];
    knowledge_categories?: Record<string, string>;
  }) {
    patch({
      knowledge_skills: next.knowledge_skills ?? ch.knowledge_skills,
      native_languages: next.native_languages ?? ch.native_languages ?? [],
      knowledge_categories: next.knowledge_categories ?? ch.knowledge_categories ?? {},
    });
  }

  return {
    owned,
    send,
    /** false when there was nothing to add: blank, or already on the sheet */
    add(name: string, category?: string): boolean {
      const trimmed = name.trim();
      if (!trimmed || owned.has(trimmed)) return false;
      const ratings = { ...ch.knowledge_skills, [trimmed]: 1 };
      const cats = { ...(ch.knowledge_categories || {}) };
      const listed = catalog.skills.knowledge.find((item) => item.name === trimmed);
      if (!listed && category) cats[trimmed] = category;
      send({ knowledge_skills: ratings, knowledge_categories: cats });
      return true;
    },
    setNative(name: string, on: boolean) {
      const ratings = { ...ch.knowledge_skills };
      const natives = [...(ch.native_languages || [])];
      const limit = Math.max(1, Number(d.native_language_limit || 1));
      if (on) {
        delete ratings[name];
        if (!natives.includes(name)) {
          if (natives.length >= limit) {
            const dropped = natives.shift();
            if (dropped) ratings[dropped] = ratings[dropped] || 1;
          }
          natives.push(name);
        }
        send({ knowledge_skills: ratings, native_languages: natives });
        return;
      }
      ratings[name] = ratings[name] || 1;
      send({
        knowledge_skills: ratings,
        native_languages: natives.filter((item) => item !== name),
      });
    },
    remove(name: string) {
      const ratings = { ...ch.knowledge_skills };
      delete ratings[name];
      const cats = { ...(ch.knowledge_categories || {}) };
      delete cats[name];
      const specs = { ...(ch.skill_specializations || {}) };
      delete specs[name];
      patch({
        knowledge_skills: ratings,
        native_languages: (ch.native_languages || []).filter((item) => item !== name),
        knowledge_categories: cats,
        skill_specializations: specs,
      });
    },
  };
}
