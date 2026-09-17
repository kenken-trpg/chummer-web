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
  "help.attr.BOD": "Body. Damage resistance, the physical monitor and the physical limit",
  "help.attr.AGI": "Agility. Most physical skills, shooting and melee; part of the physical limit",
  "help.attr.REA": "Reaction. Initiative, defense tests and piloting; part of the physical limit",
  "help.attr.STR":
    "Strength. Melee damage, throwing range and carrying; part of the physical limit",
  "help.attr.WIL": "Willpower. The stun monitor, drain resistance and the mental and social limits",
  "help.attr.LOG": "Logic. Technical skills and the Matrix; the main source of the mental limit",
  "help.attr.INT": "Intuition. Initiative, perception and defense tests; part of the mental limit",
  "help.attr.CHA":
    "Charisma. Social skills such as negotiation; the main source of the social limit",
  "help.attr.EDG": "Edge. Points per session to reroll, push the limit and so on",
  "help.attr.MAG": "Magic. The strength of spells, spirits and adept powers; drops with Essence",
  "help.attr.RES": "Resonance. The strength of complex forms and sprites; drops with Essence",
  "help.avail.what": "Availability: how hard an item is to get. Higher is harder",
  "help.avail.suffix":
    "A trailing R means a licence is needed (Restricted); F means it is illegal to own (Forbidden)",
  "help.avail.chargen":
    "At creation you cannot buy items above this availability (12 by default). In career play you roll to acquire them",
  "help.deviceRating": "The highest device rating you can buy at creation (6 by default)",
  "help.gradeHint":
    "Ware quality. Better grades cost less Essence but more nuyen and availability. Which grades are banned at creation depends on the settings (betaware and up by default)",
} as const;
