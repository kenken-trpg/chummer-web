"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { CONTACT_ROLES } from "@/lib/character/constants";

export function ContactsTab({ character: ch, d, ui, patch, setCharacter }: TabPanelProps) {
  const [contactName, setContactName] = useState("");
  const [contactRole, setContactRole] = useState("");
  const perPoint = d.contact_points?.karma_per_point ?? 1;
  const paidKarma = d.contact_points?.karma ?? d.contact_points?.paid ?? 0;

  return (
    <div className="card">
      <p className="muted">
        {ui("contact.free", {
          used: d.contact_points?.used || 0,
          free: d.contact_points?.free || 0,
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
              {item.role ? `${item.role} / ` : ""}
              Connection {item.connection} / Loyalty {item.loyalty} /{" "}
              {ui("contact.points", { points: item.cost })}
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
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, name: e.target.value } : row,
                      ),
                    })
                  }
                  onBlur={(e) =>
                    patch({
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, name: e.target.value } : row,
                      ),
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
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, role: e.target.value } : row,
                      ),
                    })
                  }
                  onBlur={(e) =>
                    patch({
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, role: e.target.value || null } : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                Connection
                <input
                  type="number"
                  min={1}
                  max={item.connection_max}
                  value={item.connection}
                  onChange={(e) =>
                    patch({
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, connection: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              <label>
                Loyalty
                <input
                  type="number"
                  min={item.loyalty_min ?? 1}
                  max={item.loyalty_max}
                  value={item.loyalty}
                  onChange={(e) =>
                    patch({
                      contacts: (ch.contacts || []).map((row) =>
                        row.id === item.id ? { ...row, loyalty: Number(e.target.value) } : row,
                      ),
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
            <option key={role} value={role} />
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
