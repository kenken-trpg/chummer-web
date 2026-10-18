"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { talentLabel } from "@/lib/character/talent-labels";
import { talentsFor } from "@/lib/character/metatype-limits";
import { sourceBit, withOriginal } from "@/lib/character/format";
import { isBookEnabled, useAllowedBooks } from "@/lib/character/books";
import { priorityTableFor } from "@/lib/character/priority-table";
import { CritterPowerRow } from "@/components/character/CritterPowerRow";

export function MetaTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const table = priorityTableFor(catalog, ch.settings?.priority_table);
  const allowedBooks = useAllowedBooks();
  const karmaBuild = ["Karma", "LifeModule"].includes(ch.build_method || "Priority");
  const choices = karmaBuild
    ? catalog.metatypes.map((m) => ({ name: m.name, special: 0, karma: m.karma ?? 0 }))
    : table.Heritage[ch.priorities.Heritage].metatypes;
  const candidates = choices.filter((choice) => {
    const spec = catalog.metatypes.find((m) => m.name === choice.name);
    return isBookEnabled(allowedBooks, spec?.source, spec?.also_in);
  });
  // The two things a metatype brings are not the same thing, and listing only
  // the second read as "a centaur's racial powers are Search and a kick".
  // Qualities are what the species grants every character of it, and they are
  // editable nowhere — the qualities tab shows them again among the purchases.
  // Critter powers exist only for the metatypes whose `<enabletab>critter`
  // reaches them, and they have no quality row at all.
  const innate = d.qualities.filter((q) => q.origin === "Metatype");
  const current = catalog.metatypes.find((m) => m.name === ch.metatype);
  // A shapeshifter's metavariant is the metahuman form it takes, and it
  // always has one: the server falls back to Human, as Chummer does.
  const shifter = current?.category === "Shapeshifter";
  // The form sets the price (Chummer charges the metavariant's karma), and
  // between forms it differs: a Bovine Elf is 10 karma at priority, its
  // Human 5. Shown for a shapeshifter only, where the form is a choice.
  const formKarma = (form: string): number | undefined =>
    karmaBuild
      ? current?.metavariants.find((v) => v.name === form)?.karma
      : table.Heritage[ch.priorities.Heritage].metatypes
          .find((m) => m.name === ch.metatype)
          ?.variants.find((v) => v.name === form)?.karma;

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("help.meta.statsLabel") })}
          lines={[
            { label: ui("help.meta.special") },
            { label: ui("help.meta.karma") },
            { label: ui("help.meta.variant") },
            { label: ui("help.meta.talent") },
          ]}
        >
          {ui("help.meta.statsLabel")}
        </HelpTip>
      </p>
      {choices.length > candidates.length ? (
        // Heritage is the first pick, and a priority row quietly short of its
        // metatypes looks like the app not having them rather than the
        // ruleset's book list leaving them out.
        <p role="status" className="muted">
          {ui("meta.booksHidden", { count: choices.length - candidates.length })}
        </p>
      ) : null}
      {!candidates.some((m) => m.name === ch.metatype) ? (
        <p role="status" className="muted">
          {ui("meta.retained", { name: tr(ch.metatype) })}
          {d.metatype_info.source ? ` / ${sourceBit(d.metatype_info, ui)}` : ""}
        </p>
      ) : null}
      <div className="grid">
        {candidates.map((m) => (
          <button
            key={m.name}
            className={`choice ${ch.metatype === m.name ? "selected" : ""}`}
            onClick={() => patch({ metatype: m.name, metavariant: null })}
          >
            <b>{tr(m.name)}</b>
            <div className="muted">
              {m.name}
              {["Karma", "LifeModule"].includes(ch.build_method || "Priority")
                ? ui("common.karmaCost", {
                    karma: ("karma" in m ? Number(m.karma) : 0) || 0,
                  })
                : ui("meta.special", { points: m.special })}
              {!["Karma", "LifeModule"].includes(ch.build_method || "Priority") &&
              (m.karma ?? 0) > 0
                ? ui("common.karmaCost", { karma: m.karma! })
                : null}
            </div>
          </button>
        ))}
      </div>
      {current?.metavariants?.length ? (
        <div style={{ marginTop: 12 }}>
          <label className="muted stacked-label">
            {ui(shifter ? "meta.metahumanForm" : "meta.metavariant")}
            <select
              value={ch.metavariant || (shifter ? "Human" : "")}
              onChange={(e) => patch({ metavariant: e.target.value || null })}
            >
              {shifter ? null : (
                <option value="">{ui("meta.noVariant", { name: tr(ch.metatype) })}</option>
              )}
              {current.metavariants.map((v) => {
                const karma = shifter ? formKarma(v.name) : undefined;
                return (
                  <option key={v.name} value={v.name}>
                    {withOriginal(v.name, tr)}
                    {karma !== undefined ? ui("common.karmaCost", { karma }) : null}
                  </option>
                );
              })}
            </select>
          </label>
        </div>
      ) : null}
      <div style={{ marginTop: 12 }}>
        <label className="muted stacked-label">
          {ui("prio.talent")}
          <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
            {talentsFor<{ name: string; label?: string }>(
              karmaBuild ? catalog.karma_talents || [] : table.Talent[ch.priorities.Talent].talents,
              ch.metatype,
              ch.talent,
              catalog,
            ).map((t) => (
              <option key={t.name} value={t.name}>
                {talentLabel(t.name, t.label, ui)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {innate.length ? (
        <section style={{ marginTop: 12 }}>
          <h3>{ui("meta.innateQualities")}</h3>
          <p className="muted">{ui("meta.innate", { name: tr(ch.metatype) })}</p>
          <ul className="critter-powers">
            {innate.map((q, index) => (
              <li key={`${q.id}-${index}`}>
                <b>{tr(q.name)}</b>{" "}
                <span className="muted">
                  {q.name}
                  {q.source ? ` / ${sourceBit(q, ui)}` : ""}
                </span>
                {q.extra ? <div className="muted">{tr(q.extra)}</div> : null}
              </li>
            ))}
          </ul>
          <p className="muted">{ui("meta.innateQualitiesHint")}</p>
        </section>
      ) : null}
      {d.metatype_info.powers?.length ? (
        <section style={{ marginTop: 12 }}>
          <h3>{ui("meta.critterPowers")}</h3>
          <p className="muted">{ui("meta.critterPowersHint")}</p>
          <ul className="critter-powers">
            {d.metatype_info.powers.map((power, index) => (
              <li key={`${power.id}-${index}`}>
                <CritterPowerRow power={power} tr={tr} ui={ui} />
                <span className="muted"> / {sourceBit(power, ui)}</span>
                {power.select ? <div className="muted">{power.select}</div> : null}
                {power.rating ? <div className="muted">{power.rating}</div> : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
