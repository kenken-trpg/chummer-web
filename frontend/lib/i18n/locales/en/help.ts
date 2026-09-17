/** Tooltip help — the formula and breakdown of computed values. English. */
export const EN_HELP = {
  "help.open": "About {label}",
  "help.base": "Base",
  "help.bonus": "Modifiers (qualities, ware, gear, …)",
  "help.bonusOther": "Other (non-stacking bonuses, …)",
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
  "help.skill.pool": "Dice pool = skill rating + linked attribute (+ modifiers)",
  "help.skill.spec": "Specialization: +2 dice on that use. 1 karma at creation, 7 in career",
  "help.skill.expertise": "Expertise: replaces the specialization for +3 dice (career only)",
  "help.skill.default":
    "A skill you have not learned can still be defaulted: the linked attribute −1 (SR5 p.130)",
  "help.skill.cap": "The rating cap at creation. One skill may sit at the cap (+1 with Aptitude)",
  "help.matrix.attack":
    "Attack: breaking into or damaging another icon. It also answers attacks made on you",
  "help.matrix.sleaze": "Sleaze: getting in and staying unnoticed; it opposes Matrix Perception",
  "help.matrix.dataprocessing":
    "Data Processing: quiet work — editing, searching, holding marks. It also drives the deck initiative",
  "help.matrix.firewall":
    "Firewall: defence against attacks and intrusions; the value that opposes them",
  "help.matrix.array":
    "A deck comes with a fixed set of four values that you assign to these slots; swapping two is a free action once per turn (SR5 p.222)",
  "help.knowledge.what":
    "Knowledge skill: linked to LOG or INT. Categories are academic, professional, interest, street and language",
  "help.knowledge.free":
    "Creation gives (INT + LOG) × 2 free points, plus one free native language",
  "help.knowledge.cost":
    "Past the free points, one karma buys one rating; a specialization is one as well",
  "help.exotic.what":
    "Exotic skill: one skill per target (a weapon type, say); the same skill can be held for several targets",
  "help.exotic.nodefault":
    "It cannot be defaulted — you need a rating to use it at all (SR5 p.130)",
  "help.essence.what":
    "Essence: how much of you is still flesh. Everyone starts at 6; cyberware and bioware spend it",
  "help.essence.magic":
    "Magic and Resonance lose what Essence loses (rounded up, one step at a time)",
  "help.essence.zero": "At 0 you die; a character must leave creation above 0",
  "help.essence.grade": "The grade multiplier (the C / B figures) changes what the same ware costs",
  "help.quality.positive": "Positive qualities cost karma — 25 karma worth at creation by default",
  "help.quality.negative": "Negative qualities give karma back, also capped at 25 karma worth",
  "help.quality.career":
    "In career play, buying or buying off a quality costs double karma (SR5 p.72)",
  "help.vehicle.statsLabel": "Stats",
  "help.vehicle.stats":
    "HND handling / SPD speed / ACC acceleration / BOD body / ARM armor / PLT pilot / SNR sensor",
  "help.vehicle.pilot":
    "Pilot is the autopilot\u2019s skill: it rolls when the vehicle acts on its own",
  "help.vehicle.body":
    "Body is toughness: damage resistance, and how many mod slots the vehicle has",
} as const;
