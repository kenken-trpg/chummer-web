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
  "help.weapon.statsLabel": "Stats",
  "help.weapon.acc": "Accuracy caps the hits that count on an attack with this weapon",
  "help.weapon.dv": "DV is the damage on a hit; a trailing P is physical, S is stun",
  "help.weapon.ap":
    "AP lowers the target\u2019s armor by that much \u2014 \u22122 means 2 less armor to resist with",
  "help.weapon.rc": "RC cancels that much of the recoil a burst builds up",
  "help.weapon.mode": "Firing modes: SS single shot, SA semi-auto, BF burst fire, FA full auto",
  "help.weapon.ammo":
    "How many rounds it holds and how it reloads: (c) clip, (m) magazine, (b) break action, (d) drum, (ml) muzzle",
  "help.weapon.reach": "Reach: in melee, the difference over your opponent is a dice bonus",
  "help.armor.statsLabel": "Armor",
  "help.armor.value": "Armor adds to the dice you resist damage with (SR5 p.169)",
  "help.armor.stack":
    "Only the highest-rated piece worn counts; the rest bring their mods along, not their rating",
  "help.armor.capacity": "Capacity is how much this piece can hold, shown as used / maximum",
  "help.armor.equipped": "A piece that is not worn does not count towards armor",
  "help.contact.statsLabel": "Ratings",
  "help.contact.connection":
    "Connection is the contact\u2019s reach and clout: what they can get you (SR5 p.388)",
  "help.contact.loyalty":
    "Loyalty is how much they care: what they will risk, and how hard they are to turn",
  "help.contact.cost":
    "At creation a contact costs Connection + Loyalty out of your contact points",
  "help.spell.statsLabel": "Spell",
  "help.spell.drain":
    "Drain is what the caster takes; F is the Force chosen when casting, so F\u22123 is Force \u2212 3 (minimum 2)",
  "help.spell.drainResist":
    "Resist drain with Willpower + your tradition\u2019s attribute; the rest is damage",
  "help.spell.force":
    "At Force up to your Magic the drain is stun damage, above it physical (SR5 p.281)",
  "help.spell.range": "Range (LOS, touch, area) and duration (instant, sustained, permanent)",
  "help.ware.statsLabel": "Ware",
  "help.ware.essence": "ESS \u2212n is the essence this piece costs, after its grade multiplier",
  "help.ware.capacity":
    "Capacity is how much this piece can hold, shown as used / maximum \u2014 cyberlimbs and housings have it",
  "help.cf.statsLabel": "Complex form",
  "help.cf.fv":
    "FV is the fading; L is the Level chosen when threading, so L\u22121 is Level \u2212 1 (minimum 2)",
  "help.cf.fade": "Resist fading with Willpower + Resonance; the rest is damage",
  "help.cf.level": "At Level up to your Resonance the fading is stun damage, above it physical",
  "help.cf.target": "What it acts on (persona, device, file, sprite, …) and how long it lasts",
  "help.spirit.statsLabel": "Spirit",
  "help.spirit.force":
    "Force is the spirit\u2019s strength: its attributes and its dice pools follow from it",
  "help.spirit.services": "Services are the tasks it still owes you \u2014 one job spends one",
  "help.spirit.bound":
    "A bound spirit can be called again but costs reagents; a summoned one leaves at dawn",
  "help.sprite.statsLabel": "Sprite",
  "help.sprite.level":
    "Level is the sprite\u2019s strength: its matrix attributes and dice pools follow from it",
  "help.sprite.tasks": "Tasks are the jobs it still owes you \u2014 one job spends one",
  "help.sprite.registered": "A registered sprite persists; a merely compiled one is gone on reboot",
  "help.initiation.statsLabel": "Grade and karma",
  "help.initiation.karma":
    "Each grade costs 10 + grade\u00d73 karma (13 for the first, 16 for the second, …)",
  "help.initiation.discount":
    "A group, an ordeal and schooling each take 10% off, and they stack (SR5 p.325)",
  "help.initiation.metamagic": "Every grade picks one metamagic or art",
  "help.life.statsLabel": "Lifestyle",
  "help.life.monthly": "Monthly = base \u00d7 (1 + modifier %) + what the lifestyle qualities add",
  "help.life.months": "That monthly figure times how long you pay for is the total",
  "help.life.lp":
    "LP is what a lifestyle you build yourself may spend on qualities, used / maximum",
} as const;
