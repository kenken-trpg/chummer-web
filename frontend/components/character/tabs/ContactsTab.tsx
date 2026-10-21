"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { CONTACT_ROLES } from "@/lib/character/constants";
import { HelpTip } from "@/components/help/HelpTip";
import { contactTerm } from "@/lib/ui-strings";
import { editRow } from "@/lib/character/rows";

export function ContactsTab({ character: ch, d, tr, ui, patch, setCharacter }: TabPanelProps) {
  const [contactName, setContactName] = useState("");
  const [contactRole, setContactRole] = useState("");
  const perPoint = d.contact_points?.karma_per_point ?? 1;
  const paidKarma = d.contact_points?.karma ?? d.contact_points?.paid ?? 0;

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("help.contact.pointsLabel") })}
          lines={[
            { label: ui("help.contact.pointsFree", { mult: d.contact_points?.free_mult ?? 3 }) },
            { label: ui("help.contact.pointsQuality") },
            { label: ui("help.contact.pointsOver") },
          ]}
        >
          {ui("help.contact.pointsLabel")}
        </HelpTip>{" "}
        {ui("contact.free", {
          used: d.contact_points?.used || 0,
          free: d.contact_points?.free || 0,
          mult: d.contact_points?.free_mult ?? 3,
        })}
        {(d.contact_points?.paid || 0) > 0
          ? ui("contact.over", { paid: d.contact_points?.paid || 0, karma: paidKarma })
          : ""}
        {ui("contact.minimum")}
        {d.career ? ui("contact.careerCap") : ui("contact.chargenCap")}
        {ui("contact.perPoint", { karma: perPoint })}
        {perPoint === 0 ? ui("contact.perPointFree") : ""}
        {ui("common.period")}
      </p>
      {(d.contacts || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{item.name || ui("common.unnamed")}</b>
            <div className="muted">
              <HelpTip
                label={ui("help.open", { label: item.name || ui("common.unnamed") })}
                lines={[
                  { label: ui("help.contact.connection") },
                  { label: ui("help.contact.loyalty") },
                  { label: ui("help.contact.cost") },
                ]}
              >
                {ui("help.contact.statsLabel")}
              </HelpTip>{" "}
              {item.role ? `${contactTerm(tr, item.role)} / ` : ""}
              {ui("contact.connection")} {item.connection} / {ui("contact.loyalty")} {item.loyalty}{" "}
              / {ui("contact.points", { points: item.cost })}
              {item.free ? ui("common.freeSlot") : ""}
              {item.group ? ui("contact.group") : ""}
              {item.billable != null && item.billable !== item.cost
                ? ui("contact.billable", { points: item.billable })
                : ""}
              {item.black_market_pipeline ? " / Black Market Pipeline" : ""}
            </div>
            <div className="cyber-controls">
              <label>
                {ui("contact.name")}
                <input
                  type="text"
                  value={(ch.contacts || []).find((row) => row.id === item.id)?.name ?? item.name}
                  onChange={(e) =>
                    setCharacter({
                      ...ch,
                      contacts: editRow(ch.contacts, item.id, { name: e.target.value }),
                    })
                  }
                  onBlur={(e) =>
                    patch({
                      contacts: editRow(ch.contacts, item.id, { name: e.target.value }),
                    })
                  }
                />
              </label>
              <label>
                {ui("contact.role")}
                <input
                  type="text"
                  list="contact-roles"
                  value={
                    (ch.contacts || []).find((row) => row.id === item.id)?.role ?? item.role ?? ""
                  }
                  onChange={(e) =>
                    setCharacter({
                      ...ch,
                      contacts: editRow(ch.contacts, item.id, { role: e.target.value }),
                    })
                  }
                  onBlur={(e) =>
                    patch({
                      contacts: editRow(ch.contacts, item.id, { role: e.target.value || null }),
                    })
                  }
                />
              </label>
              <label>
                {ui("contact.connection")}
                <input
                  type="number"
                  min={1}
                  max={item.connection_max}
                  value={item.connection}
                  onChange={(e) =>
                    patch({
                      contacts: editRow(ch.contacts, item.id, {
                        connection: Number(e.target.value),
                      }),
                    })
                  }
                />
              </label>
              <label>
                {ui("contact.loyalty")}
                <input
                  type="number"
                  min={item.loyalty_min ?? 1}
                  max={item.loyalty_max}
                  value={item.loyalty}
                  onChange={(e) =>
                    patch({
                      contacts: editRow(ch.contacts, item.id, { loyalty: Number(e.target.value) }),
                    })
                  }
                />
              </label>
            </div>
          </div>
          {item.locked ? (
            <span className="muted">{ui("common.fromQuality")}</span>
          ) : (
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  contacts: (ch.contacts || []).filter((row) => row.id !== item.id),
                })
              }
            >
              {ui("common.delete")}
            </button>
          )}
        </div>
      ))}
      <div className="cyber-toolbar">
        <input
          type="text"
          placeholder={ui("contact.name")}
          value={contactName}
          onChange={(e) => setContactName(e.target.value)}
        />
        <input
          type="text"
          list="contact-roles"
          placeholder={ui("contact.roleOptional")}
          value={contactRole}
          onChange={(e) => setContactRole(e.target.value)}
        />
        <datalist id="contact-roles">
          {[...new Set(CONTACT_ROLES)].map((role) => (
            // the value stays Chummer's English, which is what a save holds
            <option key={role} value={role} label={contactTerm(tr, role)} />
          ))}
        </datalist>
        <button
          className="btn primary"
          onClick={() => {
            const name = contactName.trim();
            patch({
              contacts: [
                ...(ch.contacts || []),
                {
                  name,
                  role: contactRole.trim() || null,
                  connection: 1,
                  loyalty: 1,
                },
              ],
            });
            setContactName("");
            setContactRole("");
          }}
        >
          {ui("common.add")}
        </button>
      </div>
    </div>
  );
}
