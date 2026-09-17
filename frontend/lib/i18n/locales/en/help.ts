/** Tooltip help — the formula and breakdown of computed values. English. */
export const EN_HELP = {
  "help.open": "About {label}",
  "help.base": "Base",
  "help.bonus": "Modifiers (qualities, ware, gear, …)",
  "help.total": "Total",
  "help.limit.physical": "Physical limit = (BOD×2 + AGI + REA + STR) ÷ 3, rounded up",
  "help.limit.mental": "Mental limit = (LOG×2 + INT + WIL) ÷ 3, rounded up",
  "help.limit.social": "Social limit = (CHA×2 + WIL + ESS) ÷ 3, rounded up",
  "help.limit.note": "Caps the hits that count on a skill test (SR5 p.47)",
  "help.cm.physical": "Physical monitor = 8 + BOD ÷ 2, rounded up",
  "help.cm.stun": "Stun monitor = 8 + WIL ÷ 2, rounded up",
  "help.cm.note": "−1 to tests for every 3 boxes filled (SR5 p.169)",
  "help.init.value": "Initiative = REA + INT",
  "help.init.dice": "Initiative dice = 1D6 + extra dice (max 5D6)",
  "help.init.note": "Turn order in combat; −10 per action phase (SR5 p.159)",
} as const;
