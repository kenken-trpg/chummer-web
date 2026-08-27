"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useState } from "react";
import { CONTACT_ROLES } from "@/lib/character/constants";

export function ContactsTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  const [contactName, setContactName] = useState("");
  const [contactRole, setContactRole] = useState("");

  return (
          <div className="card">
            <p className="muted">
              無料枠 CHA×3 = {d.contact_points?.used || 0}/{d.contact_points?.free || 0}
              {(d.contact_points?.paid || 0) > 0 ? ` ・ 超過 ${d.contact_points?.paid}カルマ` : ""}
              。Connection と Loyalty は最低1
              {d.career ? "。キャリアでは合計上限なし" : "、作成時は合計7まで"}
              。超過分は1点1カルマです。
            </p>
            {(d.contacts || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{item.name || "（無名）"}</b>
                  <div className="muted">
                    {item.role ? `${item.role} / ` : ""}
                    Connection {item.connection} / Loyalty {item.loyalty} / {item.cost}点
                  </div>
                  <div className="cyber-controls">
                    <label>
                      名前
                      <input
                        type="text"
                        value={(ch.contacts || []).find((row) => row.id === item.id)?.name ?? item.name}
                        onChange={(e) => setCharacter({
                          ...ch,
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, name: e.target.value } : row
                          )),
                        })}
                        onBlur={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, name: e.target.value } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      役割
                      <input
                        type="text"
                        list="contact-roles"
                        value={(ch.contacts || []).find((row) => row.id === item.id)?.role ?? item.role ?? ""}
                        onChange={(e) => setCharacter({
                          ...ch,
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, role: e.target.value } : row
                          )),
                        })}
                        onBlur={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, role: e.target.value || null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      Connection
                      <input
                        type="number"
                        min={1}
                        max={item.connection_max}
                        value={item.connection}
                        onChange={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, connection: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      Loyalty
                      <input
                        type="number"
                        min={1}
                        max={item.loyalty_max}
                        value={item.loyalty}
                        onChange={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, loyalty: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  contacts: (ch.contacts || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="cyber-toolbar">
              <input
                type="text"
                placeholder="名前"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
              <input
                type="text"
                list="contact-roles"
                placeholder="役割（任意）"
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
                    contacts: [...(ch.contacts || []), {
                      name,
                      role: contactRole.trim() || null,
                      connection: 1,
                      loyalty: 1,
                    }],
                  });
                  setContactName("");
                  setContactRole("");
                }}
              >
                追加
              </button>
            </div>
          </div>

  );
}
